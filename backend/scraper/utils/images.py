"""
Image Processing Utilities
Download, process, and optimize product images
"""

import asyncio
import hashlib
import io
import os
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from PIL import Image


class ImageProcessor:
    """Process and optimize product images"""
    
    # Supported formats
    SUPPORTED_FORMATS = {"jpg", "jpeg", "png", "webp", "gif"}
    
    # Default sizes for different uses
    SIZES = {
        "thumbnail": (150, 150),
        "card": (300, 300),
        "detail": (600, 600),
        "full": (1200, 1200),
    }
    
    def __init__(
        self,
        output_dir: str = "./images",
        cdn_url: Optional[str] = None,
        max_concurrent: int = 5,
    ):
        self.output_dir = output_dir
        self.cdn_url = cdn_url
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    async def download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        if not url:
            return None
        
        try:
            async with self.semaphore:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            return await response.read()
        except Exception as e:
            print(f"[ImageProcessor] Error downloading {url}: {e}")
        
        return None
    
    async def download_and_save(
        self,
        url: str,
        product_id: str,
        sizes: List[str] = None,
    ) -> dict:
        """Download image and save in multiple sizes"""
        result = {
            "original_url": url,
            "local_paths": {},
            "cdn_urls": {},
            "success": False,
        }
        
        # Download original
        image_data = await self.download_image(url)
        if not image_data:
            return result
        
        try:
            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Determine format
            original_format = img.format or "JPEG"
            ext = "jpg" if original_format == "JPEG" else original_format.lower()
            
            # Save original
            original_path = os.path.join(
                self.output_dir,
                f"{product_id}_original.{ext}"
            )
            img.save(original_path, quality=95, optimize=True)
            result["local_paths"]["original"] = original_path
            
            # Generate sizes
            sizes_to_generate = sizes or ["thumbnail", "card", "detail"]
            
            for size_name in sizes_to_generate:
                if size_name not in self.SIZES:
                    continue
                
                size = self.SIZES[size_name]
                resized = self._resize_image(img, size)
                
                path = os.path.join(
                    self.output_dir,
                    f"{product_id}_{size_name}.{ext}"
                )
                resized.save(path, quality=85, optimize=True)
                result["local_paths"][size_name] = path
                
                # Generate CDN URLs if configured
                if self.cdn_url:
                    cdn_path = f"{product_id}_{size_name}.{ext}"
                    result["cdn_urls"][size_name] = f"{self.cdn_url}/{cdn_path}"
            
            result["success"] = True
            
        except Exception as e:
            print(f"[ImageProcessor] Error processing image: {e}")
        
        return result
    
    async def process_product_images(
        self,
        product_id: str,
        image_urls: List[str],
        max_images: int = 5,
    ) -> List[dict]:
        """Process multiple images for a product"""
        results = []
        
        for i, url in enumerate(image_urls[:max_images]):
            img_id = f"{product_id}_{i}"
            result = await self.download_and_save(url, img_id)
            result["index"] = i
            results.append(result)
        
        return results
    
    def _resize_image(
        self,
        img: Image.Image,
        size: Tuple[int, int],
        method: str = "contain",
    ) -> Image.Image:
        """Resize image to target size"""
        if method == "contain":
            # Maintain aspect ratio, fit within size
            img.thumbnail(size, Image.Resampling.LANCZOS)
            return img
        
        elif method == "cover":
            # Cover the target size, crop excess
            ratio = max(size[0] / img.width, size[1] / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Crop to exact size
            left = (img.width - size[0]) // 2
            top = (img.height - size[1]) // 2
            return img.crop((left, top, left + size[0], top + size[1]))
        
        else:
            # Exact resize (may distort)
            return img.resize(size, Image.Resampling.LANCZOS)
    
    def get_image_hash(self, image_data: bytes) -> str:
        """Get hash of image for deduplication"""
        return hashlib.md5(image_data).hexdigest()
    
    def get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL"""
        parsed = urlparse(url)
        path = parsed.path
        filename = os.path.basename(path)
        
        # Clean filename
        if "?" in filename:
            filename = filename.split("?")[0]
        
        return filename or "image.jpg"
    
    def validate_image(self, image_data: bytes) -> Tuple[bool, str]:
        """Validate image data"""
        try:
            img = Image.open(io.BytesIO(image_data))
            img.verify()
            
            # Check format
            if img.format and img.format.lower() not in self.SUPPORTED_FORMATS:
                return False, f"Unsupported format: {img.format}"
            
            return True, "OK"
            
        except Exception as e:
            return False, str(e)
    
    async def cleanup_old_images(
        self,
        max_age_days: int = 30,
    ) -> int:
        """Remove old images from output directory"""
        import time
        
        removed = 0
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        try:
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        removed += 1
            
            print(f"[ImageProcessor] Removed {removed} old images")
            
        except Exception as e:
            print(f"[ImageProcessor] Error during cleanup: {e}")
        
        return removed
