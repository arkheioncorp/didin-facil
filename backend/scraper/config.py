"""
Scraper Configuration
Environment-based configuration for scraping
"""

import os
import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProxyConfig:
    """Proxy server configuration"""
    host: str
    port: int
    protocol: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_url(self) -> str:
        """Convert to proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"


@dataclass
class ScraperConfig:
    """Main scraper configuration"""
    
    # General settings
    headless: bool = True
    max_concurrent_browsers: int = 3
    request_timeout: int = 30000  # ms
    page_load_timeout: int = 60000  # ms
    
    # Rate limiting
    min_delay_between_requests: float = 2.0  # seconds
    max_delay_between_requests: float = 5.0  # seconds
    requests_per_minute: int = 20
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 5.0  # seconds
    
    # Anti-detection
    randomize_fingerprint: bool = True
    rotate_user_agents: bool = True
    simulate_human_behavior: bool = True
    
    # Safety Switch
    safety_switch_enabled: bool = True
    max_detection_rate: float = 0.2  # 20% failure rate triggers safety mode
    safety_cooldown: int = 3600  # 1 hour cooldown when safety mode is triggered
    consecutive_failures_threshold: int = 5  # Number of consecutive failures to trigger safety
    
    # Fallback
    use_fallback: bool = True
    fallback_source: str = "aliexpress"
    
    # Data settings
    max_products_per_request: int = 50
    save_images_locally: bool = False
    image_cdn_url: Optional[str] = None
    
    # Proxies
    proxies: List[ProxyConfig] = field(default_factory=list)
    
    def __post_init__(self):
        """Load configuration from environment"""
        self.headless = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
        self.max_concurrent_browsers = int(os.getenv("SCRAPER_MAX_BROWSERS", "3"))
        self.min_delay_between_requests = float(os.getenv("SCRAPER_MIN_DELAY", "2.0"))
        self.max_delay_between_requests = float(os.getenv("SCRAPER_MAX_DELAY", "5.0"))
        self.max_retries = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
        self.use_fallback = os.getenv("SCRAPER_USE_FALLBACK", "true").lower() == "true"
        self.image_cdn_url = os.getenv("CDN_URL")
        
        # Load proxies from environment
        self._load_proxies()
    
    def _load_proxies(self):
        """Load proxy list from environment or file"""
        proxy_list = os.getenv("PROXY_LIST", "")
        
        if proxy_list:
            for proxy_str in proxy_list.split(","):
                try:
                    # Format: protocol://user:pass@host:port or host:port
                    proxy = self._parse_proxy(proxy_str.strip())
                    if proxy:
                        self.proxies.append(proxy)
                except Exception as e:
                    print(f"Error parsing proxy: {e}")
        
        # Load from file if exists
        proxy_file = os.getenv("PROXY_FILE")
        if proxy_file and os.path.exists(proxy_file):
            with open(proxy_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            proxy = self._parse_proxy(line)
                            if proxy:
                                self.proxies.append(proxy)
                        except Exception:
                            pass
    
    def _parse_proxy(self, proxy_str: str) -> Optional[ProxyConfig]:
        """Parse proxy string to ProxyConfig"""
        if "://" in proxy_str:
            protocol, rest = proxy_str.split("://", 1)
        else:
            protocol = "http"
            rest = proxy_str
        
        if "@" in rest:
            auth, hostport = rest.rsplit("@", 1)
            username, password = auth.split(":", 1)
        else:
            hostport = rest
            username = password = None
        
        host, port = hostport.rsplit(":", 1)
        
        return ProxyConfig(
            host=host,
            port=int(port),
            protocol=protocol,
            username=username,
            password=password
        )


# User agent rotation list
try:
    from fake_useragent import UserAgent
    ua = UserAgent()
    def get_random_user_agent():
        return ua.random
except ImportError:
    # Fallback if fake-useragent is not installed
    def get_random_user_agent():
        return random.choice(USER_AGENTS)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Screen resolutions for fingerprinting
SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 2560, "height": 1440},
    {"width": 1680, "height": 1050},
]

# Timezone and locale combinations
LOCALES = [
    {"locale": "pt-BR", "timezone": "America/Sao_Paulo"},
    {"locale": "pt-BR", "timezone": "America/Fortaleza"},
    {"locale": "pt-BR", "timezone": "America/Manaus"},
    {"locale": "en-US", "timezone": "America/New_York"},
    {"locale": "en-US", "timezone": "America/Los_Angeles"},
]
