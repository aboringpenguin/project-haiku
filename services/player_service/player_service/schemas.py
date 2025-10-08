from pydantic import BaseModel
from datetime import datetime

class PlayerCreate(BaseModel):
    username: str
    
class PlayerResponse(BaseModel):
    id: int
    username: str
    level: int
    created_at: datetime

    class Config:
        from_attributes = True