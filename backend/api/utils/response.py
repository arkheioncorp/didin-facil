"""
Standard API Response
Uniform response structure for all endpoints
"""

from typing import Any, Generic, TypeVar, Optional
from pydantic.generics import GenericModel
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(GenericModel, Generic[T]):
    """Standard API Response Wrapper"""
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None
    meta: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard Error Response"""
    success: bool = False
    error: str
    message: str
    details: Optional[Any] = None
