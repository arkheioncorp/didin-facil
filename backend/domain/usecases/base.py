"""
Base Use Case Interface
=======================

Base class for all use cases following Command pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

# Input and Output types
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class UseCaseResult(Generic[TOutput]):
    """
    Result wrapper for use case execution.
    
    Attributes:
        success: Whether the operation succeeded
        data: The result data (if success)
        error: Error message (if failed)
        error_code: Machine-readable error code
    """
    success: bool
    data: TOutput | None = None
    error: str | None = None
    error_code: str | None = None
    
    @classmethod
    def ok(cls, data: TOutput) -> "UseCaseResult[TOutput]":
        """Create a successful result."""
        return cls(success=True, data=data)
    
    @classmethod
    def fail(
        cls, 
        error: str, 
        error_code: str = "UNKNOWN_ERROR"
    ) -> "UseCaseResult[TOutput]":
        """Create a failed result."""
        return cls(success=False, error=error, error_code=error_code)


class UseCase(ABC, Generic[TInput, TOutput]):
    """
    Abstract base class for use cases.
    
    Each use case represents a single action that can be performed.
    Implementations should:
    - Accept all dependencies via __init__
    - Implement execute() with business logic
    - Return UseCaseResult with success/failure
    
    Example:
        class CreateUserUseCase(UseCase[CreateUserInput, User]):
            def __init__(self, user_repo: UserRepository):
                self.user_repo = user_repo
            
            async def execute(self, input: CreateUserInput) -> UseCaseResult[User]:
                # Business logic here
                user = await self.user_repo.save(...)
                return UseCaseResult.ok(user)
    """
    
    @abstractmethod
    async def execute(self, input: TInput) -> UseCaseResult[TOutput]:
        """
        Execute the use case.
        
        Args:
            input: The input data for this use case
        
        Returns:
            UseCaseResult with success/failure and data
        """
        ...
