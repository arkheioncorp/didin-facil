"""
User Repository Interface
=========================

Interface para acesso a dados de usuários.
"""

from typing import List, Optional, Protocol
from uuid import UUID

from domain.entities import User
from domain.value_objects import Email


class UserRepository(Protocol):
    """
    Interface para repositório de usuários.
    
    Implementações devem ser criadas na camada de infraestrutura.
    
    Exemplo de implementação:
        class PostgresUserRepository:
            async def get_by_id(self, user_id: UUID) -> Optional[User]:
                row = await self.db.fetch_one(...)
                return self._to_entity(row)
    """
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Buscar usuário por ID.
        
        Args:
            user_id: UUID do usuário
        
        Returns:
            User se encontrado, None caso contrário
        """
        ...
    
    async def get_by_email(self, email: Email) -> Optional[User]:
        """
        Buscar usuário por email.
        
        Args:
            email: Email do usuário
        
        Returns:
            User se encontrado, None caso contrário
        """
        ...
    
    async def save(self, user: User) -> User:
        """
        Salvar usuário (criar ou atualizar).
        
        Args:
            user: Entidade User
        
        Returns:
            User salvo (com ID atualizado se criação)
        """
        ...
    
    async def delete(self, user_id: UUID) -> bool:
        """
        Deletar usuário por ID.
        
        Args:
            user_id: UUID do usuário
        
        Returns:
            True se deletado, False se não encontrado
        """
        ...
    
    async def list_active(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[User]:
        """
        Listar usuários ativos.
        
        Args:
            limit: Máximo de resultados
            offset: Offset para paginação
        
        Returns:
            Lista de usuários ativos
        """
        ...
    
    async def count_by_plan(self, plan: str) -> int:
        """
        Contar usuários por plano.
        
        Args:
            plan: Nome do plano
        
        Returns:
            Número de usuários no plano
        """
        ...
    
    async def exists(self, email: Email) -> bool:
        """
        Verificar se email já está cadastrado.
        
        Args:
            email: Email para verificar
        
        Returns:
            True se existe, False caso contrário
        """
        ...
