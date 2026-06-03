# src/core/response.py

from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

# បង្កើតអថេរតំណាងឱ្យទិន្នន័យអ្វីក៏បាន (អាចជា UserResponse, ExpertiseResponse...)
T = TypeVar('T') 

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None