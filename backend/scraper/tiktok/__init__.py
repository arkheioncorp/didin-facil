"""TikTok Scraper Module"""
# Lazy imports to avoid loading playwright at module level
# TikTokScraper and TikTokParser require playwright which may not be available
from .antibot import AntiDetection
from .api_scraper import TikTokAPIError, TikTokAPIScraper, get_api_scraper
from .data_provider import TikTokDataProvider


def get_tiktok_scraper():
    """Lazy import for TikTokScraper (requires playwright)"""
    from .scraper import TikTokScraper
    return TikTokScraper


def get_tiktok_parser():
    """Lazy import for TikTokParser (requires playwright)"""
    from .parser import TikTokParser
    return TikTokParser


__all__ = [
    "get_tiktok_scraper",
    "get_tiktok_parser",
    "AntiDetection",
    "TikTokDataProvider",
    "TikTokAPIScraper",
    "get_api_scraper",
    "TikTokAPIError",
]
