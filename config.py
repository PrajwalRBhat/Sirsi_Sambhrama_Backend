from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    
    jwt_secret: str 
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 2880  
    admin_invite_code: str 
    
    mail_username: str
    mail_password: str
    mail_from: str 

    class Config:
        env_file = ".env"

settings = Settings()