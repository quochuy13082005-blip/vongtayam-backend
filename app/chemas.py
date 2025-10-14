from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoginIn(BaseModel):
    username: str
    staff_code: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EventIn(BaseModel):
    product_code: str
    child_id: str
    message: str
    tone_score: float = 0.5
    hug_seconds: float = 0.0
    timestamp: Optional[datetime] = None



