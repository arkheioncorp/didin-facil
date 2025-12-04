# ============================================
# Profile Manager - Gerenciador de Perfis
# ============================================

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from .models import ChromeProfile

logger = logging.getLogger(__name__)


class ProfileManager:
    """
    Gerenciador de perfis Chrome para o Seller Bot.
    
    Responsável por:
    - Criar/deletar perfis isolados
    - Clonar perfil existente do usuário
    - Verificar status de login
    - Exportar/importar cookies
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Args:
            base_dir: Diretório base para armazenar perfis.
                     Default: ~/.tiktrend-facil/profiles/
        """
        self.base_dir = Path(base_dir or Path.home() / ".tiktrend-facil" / "profiles")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo de índice dos perfis
        self._index_file = self.base_dir / "profiles.json"
        self._profiles: dict[str, ChromeProfile] = {}
        
        self._load_index()
    
    def _load_index(self) -> None:
        """Carrega índice de perfis do disco"""
        if self._index_file.exists():
            try:
                with open(self._index_file) as f:
                    data = json.load(f)
                    self._profiles = {
                        k: ChromeProfile(**v) for k, v in data.items()
                    }
            except Exception as e:
                logger.error(f"Erro ao carregar índice de perfis: {e}")
                self._profiles = {}
    
    def _save_index(self) -> None:
        """Salva índice de perfis no disco"""
        try:
            with open(self._index_file, "w") as f:
                data = {k: v.model_dump(mode="json") for k, v in self._profiles.items()}
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Erro ao salvar índice de perfis: {e}")
    
    def create_profile(
        self,
        user_id: str,
        name: str,
        clone_from: Optional[str] = None,
    ) -> ChromeProfile:
        """
        Cria um novo perfil Chrome.
        
        Args:
            user_id: ID do usuário
            name: Nome amigável do perfil
            clone_from: Caminho de perfil Chrome existente para clonar
        
        Returns:
            ChromeProfile criado
        """
        profile_id = str(uuid.uuid4())
        profile_dir = self.base_dir / user_id / profile_id
        
        # Criar diretório
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Se for para clonar, copiar arquivos
        if clone_from:
            source = Path(clone_from)
            if source.exists():
                try:
                    # Copiar apenas arquivos essenciais (cookies, local storage)
                    essential_files = [
                        "Cookies",
                        "Local Storage",
                        "Session Storage",
                        "Preferences",
                        "Login Data",
                    ]
                    
                    for item in essential_files:
                        src_path = source / item
                        if src_path.exists():
                            dst_path = profile_dir / "Default" / item
                            dst_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            if src_path.is_dir():
                                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                            else:
                                shutil.copy2(src_path, dst_path)
                    
                    logger.info(f"Perfil clonado de {clone_from}")
                except Exception as e:
                    logger.error(f"Erro ao clonar perfil: {e}")
        
        profile = ChromeProfile(
            id=profile_id,
            user_id=user_id,
            name=name,
            user_data_dir=str(profile_dir),
            profile_directory="Default",
            is_logged_in=bool(clone_from),  # Assume logado se foi clonado
        )
        
        self._profiles[profile_id] = profile
        self._save_index()
        
        logger.info(f"Perfil criado: {profile_id} ({name})")
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[ChromeProfile]:
        """Obtém um perfil pelo ID"""
        return self._profiles.get(profile_id)
    
    def get_user_profiles(self, user_id: str) -> list[ChromeProfile]:
        """Obtém todos os perfis de um usuário"""
        return [p for p in self._profiles.values() if p.user_id == user_id]
    
    def delete_profile(self, profile_id: str) -> bool:
        """Deleta um perfil"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        
        try:
            # Remover diretório
            profile_path = Path(profile.user_data_dir)
            if profile_path.exists():
                shutil.rmtree(profile_path)
            
            # Remover do índice
            del self._profiles[profile_id]
            self._save_index()
            
            logger.info(f"Perfil deletado: {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar perfil: {e}")
            return False
    
    def update_last_used(self, profile_id: str) -> None:
        """Atualiza timestamp de último uso"""
        profile = self._profiles.get(profile_id)
        if profile:
            profile.last_used_at = datetime.now()
            self._save_index()
    
    def set_logged_in(self, profile_id: str, logged_in: bool) -> None:
        """Atualiza status de login"""
        profile = self._profiles.get(profile_id)
        if profile:
            profile.is_logged_in = logged_in
            self._save_index()
    
    def detect_system_chrome_profile(self) -> Optional[str]:
        """
        Detecta o perfil Chrome do sistema.
        
        Returns:
            Caminho para o diretório de dados do Chrome ou None
        """
        possible_paths = [
            # Linux
            Path.home() / ".config" / "google-chrome",
            Path.home() / ".config" / "chromium",
            # macOS
            Path.home() / "Library" / "Application Support" / "Google" / "Chrome",
            # Windows (via WSL ou similar)
            Path("/mnt/c/Users") / Path.home().name / "AppData" / "Local" / "Google" / "Chrome" / "User Data",
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "Default").exists():
                return str(path / "Default")
        
        return None
    
    async def verify_login_status(self, profile_id: str) -> bool:
        """
        Verifica se o perfil está logado no TikTok Seller.
        
        Abre o navegador brevemente para verificar.
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        
        try:
            from browser_use import Browser, BrowserProfile
            
            browser_profile = BrowserProfile(
                user_data_dir=profile.user_data_dir,
                profile_directory=profile.profile_directory,
                headless=True,
            )
            
            browser = Browser(browser_profile=browser_profile)
            page = await browser.new_page()
            
            # Navegar para TikTok Seller
            await page.goto("https://seller-br.tiktok.com")
            await asyncio.sleep(3)
            
            # Verificar se está na página de login ou no dashboard
            url = page.url
            is_logged = "login" not in url.lower() and "seller" in url.lower()
            
            await browser.close()
            
            self.set_logged_in(profile_id, is_logged)
            return is_logged
            
        except Exception as e:
            logger.error(f"Erro ao verificar login: {e}")
            return False


# Importação necessária para verify_login_status
import asyncio  # noqa: E402
