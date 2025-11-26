"""
Browser Fingerprint Generator
Generate realistic browser fingerprints to avoid detection
"""

import random
import hashlib
from typing import Dict, Any, List


class FingerprintGenerator:
    """Generate browser fingerprints for anti-detection"""
    
    # Common user agents
    USER_AGENTS = {
        "chrome_windows": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        ],
        "chrome_mac": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ],
        "firefox_windows": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
            "Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) "
            "Gecko/20100101 Firefox/120.0",
        ],
        "safari_mac": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ],
    }
    
    # Screen resolutions by popularity
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080, "weight": 30},
        {"width": 1366, "height": 768, "weight": 20},
        {"width": 1536, "height": 864, "weight": 15},
        {"width": 1440, "height": 900, "weight": 10},
        {"width": 1280, "height": 720, "weight": 8},
        {"width": 2560, "height": 1440, "weight": 7},
        {"width": 1680, "height": 1050, "weight": 5},
        {"width": 3840, "height": 2160, "weight": 5},
    ]
    
    # WebGL vendors and renderers
    WEBGL_CONFIGS = [
        {
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)"
        },
        {
            "vendor": "Google Inc. (Intel)",
            "renderer": "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"
        },
        {
            "vendor": "Google Inc. (AMD)",
            "renderer": "ANGLE (AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)"
        },
        {
            "vendor": "Intel Inc.",
            "renderer": "Intel Iris OpenGL Engine"
        },
        {
            "vendor": "Apple Inc.",
            "renderer": "AMD Radeon Pro 5500M OpenGL Engine"
        },
    ]
    
    # Brazilian locales and timezones
    BR_LOCALES = [
        {"locale": "pt-BR", "timezone": "America/Sao_Paulo", "city": "São Paulo"},
        {"locale": "pt-BR", "timezone": "America/Fortaleza", "city": "Fortaleza"},
        {"locale": "pt-BR", "timezone": "America/Manaus", "city": "Manaus"},
        {"locale": "pt-BR", "timezone": "America/Recife", "city": "Recife"},
        {"locale": "pt-BR", "timezone": "America/Bahia", "city": "Salvador"},
    ]
    
    # US locales
    US_LOCALES = [
        {"locale": "en-US", "timezone": "America/New_York", "city": "New York"},
        {"locale": "en-US", "timezone": "America/Los_Angeles", "city": "Los Angeles"},
        {"locale": "en-US", "timezone": "America/Chicago", "city": "Chicago"},
    ]
    
    def __init__(self, prefer_brazilian: bool = True):
        self.prefer_brazilian = prefer_brazilian
        self.used_fingerprints: List[str] = []
    
    def generate(self) -> Dict[str, Any]:
        """Generate a complete browser fingerprint"""
        # Select user agent type
        ua_type = random.choice(list(self.USER_AGENTS.keys()))
        user_agent = random.choice(self.USER_AGENTS[ua_type])
        
        # Select screen resolution (weighted)
        screen = self._weighted_choice(self.SCREEN_RESOLUTIONS)
        
        # Select locale/timezone
        if self.prefer_brazilian:
            locale_data = random.choice(self.BR_LOCALES)
        else:
            all_locales = self.BR_LOCALES + self.US_LOCALES
            locale_data = random.choice(all_locales)
        
        # Select WebGL config
        webgl = random.choice(self.WEBGL_CONFIGS)
        
        # Generate fingerprint
        fingerprint = {
            "user_agent": user_agent,
            "platform": self._get_platform(ua_type),
            "vendor": self._get_vendor(ua_type),
            "screen": {
                "width": screen["width"],
                "height": screen["height"],
                "availWidth": screen["width"],
                "availHeight": screen["height"] - 40,  # Taskbar
                "colorDepth": random.choice([24, 32]),
                "pixelDepth": random.choice([24, 32]),
            },
            "locale": locale_data["locale"],
            "timezone": locale_data["timezone"],
            "city": locale_data["city"],
            "languages": self._get_languages(locale_data["locale"]),
            "webgl": webgl,
            "hardware": {
                "deviceMemory": random.choice([4, 8, 16, 32]),
                "hardwareConcurrency": random.choice([4, 8, 12, 16]),
                "maxTouchPoints": 0 if "Windows" in user_agent else random.choice([0, 5]),
            },
            "audio": {
                "sampleRate": random.choice([44100, 48000]),
                "channelCount": 2,
            },
            "canvas_noise": random.random() * 0.0001,
            "fonts": self._get_common_fonts(ua_type),
            "do_not_track": random.choice([None, "1"]),
        }
        
        # Generate unique hash for this fingerprint
        fp_hash = self._hash_fingerprint(fingerprint)
        
        # Avoid duplicates
        if fp_hash in self.used_fingerprints:
            return self.generate()  # Try again
        
        self.used_fingerprints.append(fp_hash)
        fingerprint["hash"] = fp_hash
        
        return fingerprint
    
    def generate_for_playwright(self) -> Dict[str, Any]:
        """Generate fingerprint formatted for Playwright context"""
        fp = self.generate()
        
        return {
            "viewport": {
                "width": fp["screen"]["width"],
                "height": fp["screen"]["height"],
            },
            "user_agent": fp["user_agent"],
            "locale": fp["locale"],
            "timezone_id": fp["timezone"],
            "color_scheme": random.choice(["light", "dark"]),
            "device_scale_factor": random.choice([1, 1.25, 1.5, 2]),
            "has_touch": fp["hardware"]["maxTouchPoints"] > 0,
            "extra_http_headers": {
                "Accept-Language": ",".join(fp["languages"]),
            },
        }
    
    def _get_platform(self, ua_type: str) -> str:
        """Get platform string for user agent type"""
        if "windows" in ua_type:
            return "Win32"
        elif "mac" in ua_type:
            return "MacIntel"
        elif "linux" in ua_type:
            return "Linux x86_64"
        return "Win32"
    
    def _get_vendor(self, ua_type: str) -> str:
        """Get browser vendor"""
        if "chrome" in ua_type:
            return "Google Inc."
        elif "firefox" in ua_type:
            return ""
        elif "safari" in ua_type:
            return "Apple Computer, Inc."
        return "Google Inc."
    
    def _get_languages(self, locale: str) -> List[str]:
        """Get language list for locale"""
        if locale.startswith("pt"):
            return ["pt-BR", "pt", "en-US", "en"]
        return ["en-US", "en"]
    
    def _get_common_fonts(self, ua_type: str) -> List[str]:
        """Get common fonts for platform"""
        common = [
            "Arial",
            "Arial Black",
            "Comic Sans MS",
            "Courier New",
            "Georgia",
            "Impact",
            "Times New Roman",
            "Trebuchet MS",
            "Verdana",
        ]
        
        if "windows" in ua_type:
            common.extend([
                "Calibri",
                "Cambria",
                "Consolas",
                "Segoe UI",
            ])
        elif "mac" in ua_type:
            common.extend([
                "Helvetica",
                "Helvetica Neue",
                "Menlo",
                "Monaco",
                "San Francisco",
            ])
        
        # Return random subset
        return random.sample(common, k=min(len(common), 8))
    
    def _weighted_choice(self, items: List[Dict]) -> Dict:
        """Choose item based on weight"""
        total = sum(item.get("weight", 1) for item in items)
        r = random.uniform(0, total)
        
        cumulative = 0
        for item in items:
            cumulative += item.get("weight", 1)
            if r <= cumulative:
                return item
        
        return items[-1]
    
    def _hash_fingerprint(self, fp: Dict) -> str:
        """Generate unique hash for fingerprint"""
        key_parts = [
            fp["user_agent"],
            str(fp["screen"]["width"]),
            str(fp["screen"]["height"]),
            fp["locale"],
            fp["timezone"],
            str(fp["hardware"]["deviceMemory"]),
        ]
        
        data = "|".join(key_parts)
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def clear_history(self) -> None:
        """Clear used fingerprints history"""
        self.used_fingerprints.clear()
