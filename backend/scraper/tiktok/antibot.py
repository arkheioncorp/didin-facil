"""
Anti-Detection Strategies
Browser fingerprint randomization and stealth techniques
"""

import random
from typing import Dict, Any

from ..config import SCREEN_RESOLUTIONS, LOCALES


class AntiDetection:
    """Anti-detection and fingerprint randomization"""
    
    def __init__(self):
        self.used_fingerprints = []
    
    def generate_fingerprint(self) -> Dict[str, Any]:
        """Generate a random browser fingerprint"""
        from ..config import get_random_user_agent
        user_agent = get_random_user_agent()
        screen = random.choice(SCREEN_RESOLUTIONS)
        locale_data = random.choice(LOCALES)
        
        fingerprint = {
            "user_agent": user_agent,
            "screen": screen,
            "locale": locale_data["locale"],
            "timezone": locale_data["timezone"],
            "platform": self._get_platform_from_ua(user_agent),
            "vendor": self._get_vendor_from_ua(user_agent),
            "webgl_vendor": self._random_webgl_vendor(),
            "webgl_renderer": self._random_webgl_renderer(),
            "languages": self._get_languages(locale_data["locale"]),
            "color_depth": random.choice([24, 32]),
            "device_memory": random.choice([4, 8, 16]),
            "hardware_concurrency": random.choice([4, 8, 12, 16]),
            "geolocation": self._get_geolocation(locale_data["timezone"]),
        }
        
        self.used_fingerprints.append(fingerprint)
        return fingerprint
    
    def _get_platform_from_ua(self, user_agent: str) -> str:
        """Extract platform from user agent"""
        if "Windows" in user_agent:
            return "Win32"
        elif "Mac" in user_agent:
            return "MacIntel"
        elif "Linux" in user_agent:
            return "Linux x86_64"
        return "Win32"
    
    def _get_vendor_from_ua(self, user_agent: str) -> str:
        """Get browser vendor from user agent"""
        if "Chrome" in user_agent or "Chromium" in user_agent:
            return "Google Inc."
        elif "Firefox" in user_agent:
            return ""
        elif "Safari" in user_agent:
            return "Apple Computer, Inc."
        return "Google Inc."
    
    def _random_webgl_vendor(self) -> str:
        """Random WebGL vendor"""
        vendors = [
            "Google Inc. (NVIDIA)",
            "Google Inc. (Intel)",
            "Google Inc. (AMD)",
            "Intel Inc.",
            "NVIDIA Corporation",
        ]
        return random.choice(vendors)
    
    def _random_webgl_renderer(self) -> str:
        """Random WebGL renderer"""
        renderers = [
            "ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)",
            "Intel Iris OpenGL Engine",
            "AMD Radeon Pro 5500M OpenGL Engine",
        ]
        return random.choice(renderers)
    
    def _get_languages(self, locale: str) -> list:
        """Get language list for locale"""
        if locale.startswith("pt"):
            return ["pt-BR", "pt", "en-US", "en"]
        return ["en-US", "en"]
    
    def _get_geolocation(self, timezone: str) -> dict:
        """Get approximate geolocation for timezone"""
        locations = {
            "America/Sao_Paulo": {"latitude": -23.5505, "longitude": -46.6333},
            "America/Fortaleza": {"latitude": -3.7172, "longitude": -38.5433},
            "America/Manaus": {"latitude": -3.1190, "longitude": -60.0217},
            "America/New_York": {"latitude": 40.7128, "longitude": -74.0060},
            "America/Los_Angeles": {"latitude": 34.0522, "longitude": -118.2437},
        }
        
        base = locations.get(timezone, locations["America/Sao_Paulo"])
        
        # Add small random offset
        return {
            "latitude": base["latitude"] + random.uniform(-0.1, 0.1),
            "longitude": base["longitude"] + random.uniform(-0.1, 0.1),
        }
    
    def get_stealth_script(self) -> str:
        """Get JavaScript to inject for stealth mode"""
        return """
        // Override webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' },
                ];
                const pluginArray = [];
                plugins.forEach((p, i) => {
                    pluginArray[i] = p;
                    pluginArray[p.name] = p;
                });
                pluginArray.length = plugins.length;
                pluginArray.item = (i) => plugins[i];
                pluginArray.namedItem = (name) => plugins.find(p => p.name === name);
                pluginArray.refresh = () => {};
                return pluginArray;
            },
            configurable: true
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            configurable: true
        });
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Randomize canvas fingerprint
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(...args) {
            const imageData = originalGetImageData.apply(this, args);
            // Add subtle noise
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 3) - 1;     // R
                imageData.data[i + 1] += Math.floor(Math.random() * 3) - 1; // G
                imageData.data[i + 2] += Math.floor(Math.random() * 3) - 1; // B
            }
            return imageData;
        };
        
        // Override toDataURL
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(...args) {
            const context = this.getContext('2d');
            if (context) {
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] += Math.floor(Math.random() * 2);
                }
                context.putImageData(imageData, 0, 0);
            }
            return originalToDataURL.apply(this, args);
        };
        
        // WebGL fingerprint protection
        const getParameterProxyHandler = {
            apply: function(target, thisArg, argumentsList) {
                const param = argumentsList[0];
                const gl = thisArg;
                
                // Randomize some WebGL parameters
                if (param === 37445) { // UNMASKED_VENDOR_WEBGL
                    return 'Google Inc. (NVIDIA)';
                }
                if (param === 37446) { // UNMASKED_RENDERER_WEBGL
                    return 'ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)';
                }
                
                return Reflect.apply(target, thisArg, argumentsList);
            }
        };
        
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                const originalGetParameter = gl.getParameter.bind(gl);
                gl.getParameter = new Proxy(originalGetParameter, getParameterProxyHandler);
            }
        } catch (e) {}
        
        // Override chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Remove automation indicators
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        
        console.log('[Stealth] Anti-detection scripts loaded');
        """
    
    def get_mouse_movement_script(self) -> str:
        """Get script for simulating mouse movements"""
        return """
        (function() {
            const movements = [];
            const startX = Math.random() * window.innerWidth;
            const startY = Math.random() * window.innerHeight;
            
            // Generate bezier curve points
            for (let i = 0; i < 20; i++) {
                const t = i / 20;
                const x = startX + (Math.random() - 0.5) * 200 * t;
                const y = startY + (Math.random() - 0.5) * 200 * t;
                movements.push({ x, y, delay: 50 + Math.random() * 100 });
            }
            
            // Dispatch mouse events
            let index = 0;
            function moveNext() {
                if (index >= movements.length) return;
                
                const { x, y, delay } = movements[index];
                const event = new MouseEvent('mousemove', {
                    clientX: x,
                    clientY: y,
                    bubbles: true
                });
                document.dispatchEvent(event);
                
                index++;
                setTimeout(moveNext, delay);
            }
            
            moveNext();
        })();
        """
