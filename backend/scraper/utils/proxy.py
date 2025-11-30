"""
Proxy Pool Manager
Rotating proxy management for scraping
"""

import random
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone


@dataclass
class ProxyStats:
    """Statistics for a proxy"""
    success_count: int = 0
    failure_count: int = 0
    total_requests: int = 0
    last_used: Optional[datetime] = None
    avg_response_time: float = 0.0
    is_blocked: bool = False
    blocked_until: Optional[datetime] = None


class ProxyPool:
    """
    Rotating proxy pool with health tracking
    Supports HTTP, HTTPS, and SOCKS5 proxies
    """
    
    def __init__(self, proxies: List = None):
        """
        Initialize proxy pool
        
        Args:
            proxies: List of ProxyConfig objects or proxy URLs
        """
        self.proxies: List[Dict] = []
        self.stats: Dict[str, ProxyStats] = {}
        self.current_index = 0
        
        if proxies:
            for proxy in proxies:
                self.add_proxy(proxy)
    
    def add_proxy(self, proxy) -> None:
        """Add a proxy to the pool"""
        if hasattr(proxy, 'to_url'):
            # ProxyConfig object
            proxy_url = proxy.to_url()
            proxy_dict = {
                "server": proxy_url,
                "username": proxy.username,
                "password": proxy.password,
            }
        elif isinstance(proxy, str):
            # URL string
            proxy_dict = self._parse_proxy_url(proxy)
        elif isinstance(proxy, dict):
            proxy_dict = proxy
        else:
            return
        
        if proxy_dict and proxy_dict.get("server"):
            self.proxies.append(proxy_dict)
            self.stats[proxy_dict["server"]] = ProxyStats()
    
    def _parse_proxy_url(self, url: str) -> Optional[Dict]:
        """Parse proxy URL to dict"""
        try:
            # Format: protocol://user:pass@host:port
            if "://" in url:
                protocol, rest = url.split("://", 1)
            else:
                protocol = "http"
                rest = url
            
            username = password = None
            if "@" in rest:
                auth, hostport = rest.rsplit("@", 1)
                if ":" in auth:
                    username, password = auth.split(":", 1)
            else:
                hostport = rest
            
            return {
                "server": f"{protocol}://{hostport}",
                "username": username,
                "password": password,
            }
        except Exception:
            return None
    
    def has_proxies(self) -> bool:
        """Check if pool has available proxies"""
        return len(self.get_available_proxies()) > 0
    
    def get_available_proxies(self) -> List[Dict]:
        """Get list of available (non-blocked) proxies"""
        available = []
        now = datetime.now(timezone.utc)
        
        for proxy in self.proxies:
            stats = self.stats.get(proxy["server"])
            
            if stats and stats.is_blocked:
                # Check if block has expired
                if stats.blocked_until and now > stats.blocked_until:
                    stats.is_blocked = False
                    stats.blocked_until = None
                else:
                    continue
            
            available.append(proxy)
        
        return available
    
    def get_next(self) -> Optional[Dict]:
        """Get next proxy using round-robin"""
        available = self.get_available_proxies()
        
        if not available:
            return None
        
        self.current_index = (self.current_index + 1) % len(available)
        proxy = available[self.current_index]
        
        # Update stats
        stats = self.stats.get(proxy["server"])
        if stats:
            stats.last_used = datetime.now(timezone.utc)
            stats.total_requests += 1
        
        return proxy
    
    def get_random(self) -> Optional[Dict]:
        """Get a random available proxy"""
        available = self.get_available_proxies()
        
        if not available:
            return None
        
        proxy = random.choice(available)
        
        # Update stats
        stats = self.stats.get(proxy["server"])
        if stats:
            stats.last_used = datetime.now(timezone.utc)
            stats.total_requests += 1
        
        return proxy
    
    def get_best(self) -> Optional[Dict]:
        """Get proxy with best success rate"""
        available = self.get_available_proxies()
        
        if not available:
            return None
        
        # Sort by success rate
        def success_rate(p):
            s = self.stats.get(p["server"])
            if not s or s.total_requests == 0:
                return 0.5  # Neutral for unused
            return s.success_count / s.total_requests
        
        proxy = max(available, key=success_rate)
        
        # Update stats
        stats = self.stats.get(proxy["server"])
        if stats:
            stats.last_used = datetime.now(timezone.utc)
            stats.total_requests += 1
        
        return proxy
    
    def report_success(
        self, 
        proxy: Dict, 
        response_time: float = 0.0
    ) -> None:
        """Report successful request"""
        server = proxy.get("server")
        if server not in self.stats:
            return
        
        stats = self.stats[server]
        stats.success_count += 1
        
        # Update average response time
        if response_time > 0:
            total = stats.avg_response_time * (stats.success_count - 1)
            stats.avg_response_time = (total + response_time) / stats.success_count
    
    def report_failure(
        self, 
        proxy: Dict, 
        block_minutes: int = 0
    ) -> None:
        """Report failed request"""
        server = proxy.get("server")
        if server not in self.stats:
            return
        
        stats = self.stats[server]
        stats.failure_count += 1
        
        # Auto-block if too many failures
        failure_rate = stats.failure_count / max(stats.total_requests, 1)
        
        if failure_rate > 0.5 and stats.total_requests >= 5:
            self.block_proxy(proxy, block_minutes or 30)
        elif block_minutes > 0:
            self.block_proxy(proxy, block_minutes)
    
    def block_proxy(self, proxy: Dict, minutes: int = 30) -> None:
        """Temporarily block a proxy"""
        server = proxy.get("server")
        if server not in self.stats:
            return
        
        stats = self.stats[server]
        stats.is_blocked = True
        stats.blocked_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        
        print(f"[Proxy Pool] Blocked {server} for {minutes} minutes")
    
    def unblock_proxy(self, proxy: Dict) -> None:
        """Unblock a proxy"""
        server = proxy.get("server")
        if server not in self.stats:
            return
        
        stats = self.stats[server]
        stats.is_blocked = False
        stats.blocked_until = None
    
    def get_stats(self) -> Dict:
        """Get pool statistics"""
        total = len(self.proxies)
        available = len(self.get_available_proxies())
        blocked = total - available
        
        total_requests = sum(s.total_requests for s in self.stats.values())
        total_success = sum(s.success_count for s in self.stats.values())
        
        return {
            "total_proxies": total,
            "available_proxies": available,
            "blocked_proxies": blocked,
            "total_requests": total_requests,
            "total_success": total_success,
            "success_rate": total_success / max(total_requests, 1),
        }
    
    def reset_stats(self) -> None:
        """Reset all proxy statistics"""
        for server in self.stats:
            self.stats[server] = ProxyStats()
        
        print("[Proxy Pool] Stats reset")
