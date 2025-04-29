from typing import Optional
from pydantic import BaseModel, EmailStr

class UserInfoRequest(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    mother_language: str
    gender: str
    job_title: str
    birth_year: str
    remember_me: Optional[bool] = None