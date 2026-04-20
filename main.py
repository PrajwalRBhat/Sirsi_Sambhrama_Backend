from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from typing import Optional
from database import supabase
from config import settings
import schemas
import auth

app = FastAPI(
    title="Sirsi Sambhrama Admin API",
    description="Backend API for managing Sirsi Sambhrama news editors and content.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["General"])
def home():
    return {"status": "Online", "message": "The Sirsi Sambhrama Backend is ALIVE!"}


@app.post("/register/request", tags=["Authentication"])
def register_request(editor_data: schemas.EditorCreate):
    
    current_time = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("Editor Information").delete().eq("is_active", False).lt("otp_expiry", current_time).execute()
    except Exception as e:
        print(f"JANITOR ERROR (Ignored): {e}")

    if editor_data.invite_code != settings.admin_invite_code:
        raise HTTPException(status_code=403, detail="Invalid Invite Code")

    hashed_pw = auth.hash_password(editor_data.password)
    otp = auth.generate_otp()
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    
    new_editor = {
        "email": editor_data.email,
        "password_hash": hashed_pw,
        "auth_name": editor_data.auth_name,
        "otp_code": otp,
        "otp_expiry": expiry,
        "role": "journalist",
        "is_active": False 
    }

    try:
        supabase.table("Editor Information").insert(new_editor).execute()
        auth.send_otp_email(editor_data.email, otp)
        return {"message": "Registration initiated. Check your email for OTP."}
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        raise HTTPException(status_code=400, detail="Registration failed. Email might already exist.")


@app.post("/register/verify", tags=["Authentication"])
def verify_registration(data: schemas.OTPVerify):
    response = supabase.table("Editor Information").select("*").eq("email", data.email).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    editor = response.data[0]

    if editor.get("otp_code") != data.otp_code:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    supabase.table("Editor Information").update({
        "is_active": True,
        "otp_code": None,
        "otp_expiry": None
    }).eq("email", data.email).execute()

    return {"message": "Account verified and activated! You can now log in."}


@app.post("/login", response_model=schemas.Token, tags=["Authentication"])
def login(login_data: schemas.EditorLogin):
    response = supabase.table("Editor Information").select("*").eq("email", login_data.email).execute()
    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    editor = response.data[0]

    if not editor.get("is_active"):
        raise HTTPException(status_code=403, detail="Account not verified. Please verify via OTP.")

    if not auth.verify_password(login_data.password, editor["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth.create_access_token(
        data={
            "sub": editor["email"], 
            "role": editor.get("role", "journalist"),
            "name": editor.get("auth_name") 
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/forgot-password", tags=["Password Recovery"])
def forgot_password(data: schemas.EditorLogin): 
    response = supabase.table("Editor Information").select("*").eq("email", data.email).execute()
    if not response.data:
        return {"message": "If this email is registered, an OTP has been sent."}

    otp = auth.generate_otp()
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    supabase.table("Editor Information").update({
        "otp_code": otp,
        "otp_expiry": expiry
    }).eq("email", data.email).execute()

    try:
        auth.send_otp_email(data.email, otp)
        return {"message": "OTP sent to your registered email."}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send email.")


@app.post("/auth/reset-password", tags=["Password Recovery"])
def reset_password(data: schemas.PasswordReset):
    response = supabase.table("Editor Information").select("*").eq("email", data.email).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    editor = response.data[0]

    if editor.get("otp_code") != data.otp_code:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    expiry_str = editor.get("otp_expiry")
    if expiry_str and datetime.now(timezone.utc) > datetime.fromisoformat(expiry_str):
        raise HTTPException(status_code=401, detail="OTP has expired")

    new_hashed_pw = auth.hash_password(data.new_password)

    supabase.table("Editor Information").update({
        "password_hash": new_hashed_pw,
        "otp_code": None,
        "otp_expiry": None
    }).eq("email", data.email).execute()

    return {"message": "Password updated successfully! You can now log in."}

@app.patch("/auth/update-name", tags=["Authentication"])
def update_pen_name(data: schemas.NameUpdate, user = Depends(auth.get_current_user)):
    email = user.get("sub")
    
    try:
        supabase.table("Editor Information").update({"auth_name": data.new_name}).eq("email", email).execute()
        
        supabase.table("News Articles").update({"pen_name": data.new_name}).eq("editor_email", email).execute()
        
        return {"message": "Name updated successfully!"}
    except Exception as e:
        print(f"NAME UPDATE ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to update name.")


@app.post("/news/create", tags=["News"])
def create_article_with_image(
    title: str = Form(...),
    article: str = Form(...),
    category: schemas.NewsCategory = Form(...),  
    image_cap: str = Form(...),          
    is_trending: bool = Form(False),
    is_breaking: bool = Form(False),
    is_published: bool = Form(False),
    image_file: UploadFile = File(...), 
    user = Depends(auth.get_current_user)
):
    
    if not image_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")

    try:
        file_extension = image_file.filename.split(".")[-1]
        unique_filename = f"{datetime.now(timezone.utc).timestamp()}.{file_extension}"
        file_content = image_file.file.read()

        supabase.storage.from_("news_images").upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": image_file.content_type}
        )
        
        generated_url = supabase.storage.from_("news_images").get_public_url(unique_filename)

        new_article = {
            "title": title,
            "article": article,
            "category": category.value, 
            "pen_name": user.get("name"),       
            "editor_email": user.get("sub"),    
            "image_url": generated_url, 
            "image_cap": image_cap,
            "is_trending": is_trending,
            "is_breaking": is_breaking,
            "is_published": is_published
        }

        response = supabase.table("News Articles").insert(new_article).execute()
        
        return {
            "message": "Article published successfully!",
            "article_id": response.data[0]["id"],
            "image_link": generated_url
        }

    except Exception as e:
        print(f"NEWS CREATION ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image or save to database.")

@app.get("/news/me", response_model=list[schemas.NewsResponse], tags=["News"])
def get_my_articles(user = Depends(auth.get_current_user)):
    
    response = supabase.table("News Articles").select("*").eq("editor_email", user.get("sub")).order("display_date", desc=True).execute()
    return response.data

@app.delete("/news/{article_id}", tags=["News"])
def delete_article(article_id: int, user = Depends(auth.get_current_user)):
    
    response = supabase.table("News Articles").select("image_url, editor_email").eq("id", article_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Article not found.")
        
    article_data = response.data[0]
    
    if article_data.get("editor_email") != user.get("sub") and user.get("role") != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Security violation: You can only delete your own articles."
        )
        
    image_url = article_data.get("image_url")
    
    try:
        if image_url:
            filename = image_url.split("/")[-1]
            supabase.storage.from_("news_images").remove([filename])
            
        supabase.table("News Articles").delete().eq("id", article_id).execute()
        
        return {"message": f"Article {article_id} and its image were successfully deleted."}

    except Exception as e:
        print(f"DELETE ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete article or image.")

@app.patch("/news/{article_id}", tags=["News"])
def update_article(
    article_id: int,
    title: Optional[str] = Form(None),
    article: Optional[str] = Form(None),
    category: Optional[schemas.NewsCategory] = Form(None),
    image_cap: Optional[str] = Form(None),
    is_trending: Optional[bool] = Form(None),
    is_breaking: Optional[bool] = Form(None),
    is_published: Optional[bool] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    user = Depends(auth.get_current_user)
):
    
    response = supabase.table("News Articles").select("*").eq("id", article_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Article not found.")
    
    existing_article = response.data[0]

    if existing_article.get("editor_email") != user.get("sub") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You can only edit your own work.")

    update_data = {}
    
    if title: update_data["title"] = title
    if article: update_data["article"] = article
    if category: update_data["category"] = category.value
    if image_cap: update_data["image_cap"] = image_cap
    
    if is_trending is not None: update_data["is_trending"] = is_trending
    if is_breaking is not None: update_data["is_breaking"] = is_breaking
    if is_published is not None: update_data["is_published"] = is_published

    if image_file:
        try:
            old_url = existing_article.get("image_url")
            if old_url:
                old_filename = old_url.split("/")[-1]
                supabase.storage.from_("news_images").remove([old_filename])

            file_ext = image_file.filename.split(".")[-1]
            new_filename = f"{datetime.now(timezone.utc).timestamp()}.{file_ext}"
            
            content = image_file.file.read()
            
            supabase.storage.from_("news_images").upload(
                path=new_filename,
                file=content,
                file_options={"content-type": image_file.content_type}
            )
            
            update_data["image_url"] = supabase.storage.from_("news_images").get_public_url(new_filename)
        except Exception as e:
            print(f"PATCH IMAGE ERROR: {e}")
            raise HTTPException(status_code=500, detail="Failed to swap images.")

    if update_data:
        supabase.table("News Articles").update(update_data).eq("id", article_id).execute()
        return {"message": "Update successful", "changed": list(update_data.keys())}
    
    return {"message": "Nothing changed."}