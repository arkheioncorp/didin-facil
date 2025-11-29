# ============================================
# Profile Models - Modelos de Perfis Chrome
# ============================================

from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class ChromeProfile(BaseModel):
    """Perfil Chrome para automação"""
    
    # Identificação
    id: str = Field(..., description="ID único do perfil")
    user_id: str = Field(..., description="ID do usuário dono do perfil")
    name: str = Field(..., description="Nome amigável do perfil")
    
    # Caminhos
    user_data_dir: str = Field(..., description="Diretório de dados do Chrome")
    profile_directory: str = Field(default="Default", description="Subdiretório do perfil")
    
    # Estado
    is_logged_in: bool = Field(default=False, description="Se está logado no TikTok Seller")
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Configurações
    platform: str = Field(default="tiktok_seller", description="Plataforma alvo")
    cookies_exported: bool = Field(default=False, description="Se os cookies foram exportados")
    
    @property
    def full_path(self) -> Path:
        """Retorna o caminho completo do perfil"""
        return Path(self.user_data_dir) / self.profile_directory
    
    @property
    def exists(self) -> bool:
        """Verifica se o perfil existe no disco"""
        return self.full_path.exists()


class ProfileCredentials(BaseModel):
    """Credenciais armazenadas (criptografadas)"""
    
    profile_id: str
    platform: str
    username: Optional[str] = None
    # Nota: Senhas nunca são armazenadas
    # Usamos cookies/session persistente
    
    # Tokens de sessão (se disponíveis)
    session_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
