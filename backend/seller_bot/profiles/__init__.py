# Profiles Module - Gestão de Perfis Chrome

from .manager import ProfileManager
from .models import ChromeProfile

__all__ = [
    "ProfileManager",
    "ChromeProfile",
]
