from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class NewsCategory(str, Enum):
    SPORTS = "Sports"
    LOCAL = "Local"
    HEALTH = "Health"
    POLITICS = "Politics"

class EditorCreate(BaseModel):
    email: EmailStr
    password: str
    auth_name: str
    invite_code: str

class EditorLogin(BaseModel):
    email: EmailStr
    password: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str

class PasswordReset(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class NameUpdate(BaseModel):
    new_name: str

class NewsBase(BaseModel):
    title: str
    article: str  
    image_url: str              
    image_cap: str              
    category: NewsCategory        
    pen_name: str                 
    editor_email: str             
    is_trending: bool = False
    is_breaking: bool = False
    is_published: bool = False

    class Config:
        from_attributes = True

class NewsCreate(NewsBase):
    pass

class NewsResponse(NewsBase):
    id: int
    display_date: datetime 