# Sirsi Sambhrama Backend API

A high-performance, secure RESTful API built with **FastAPI** to power the Sirsi Sambhrama news platform. This backend manages journalist workflows, real-time news updates, and secure cloud-based data persistence.

## 🚀 Live Demo
- **Interactive API Docs (Swagger):** [https://sirsi-sambhrama-backend.onrender.com/docs](https://sirsi-sambhrama-backend.onrender.com/docs)
- **Frontend Live Site:** [Your-Netlify-URL-Here]

## 🛠️ Tech Stack
- **Framework:** FastAPI (Python 3.12+)
- **Security:** **Argon2-id** (Password Hashing), JWT (Session Management)
- **Database:** PostgreSQL (via Supabase)
- **Email Engine:** Gmail SMTP API for OTP Delivery
- **Deployment:** Render (Cloud Backend) & Netlify (Frontend)
- **Data Validation:** Pydantic v2

## ✨ Key Features
- **Advanced Security:** - Industry-standard **Argon2-id** hashing for credential protection.
  - Two-step verification via OTP sent to journalist emails.
  - Admin-only registration gated by a private invite code.
- **Content Management (CRUD):** - Full article lifecycle (Draft, Publish, Trending, Breaking News).
  - Automated image URL handling and metadata management.
- **Journalist Workspace:** - Personal dashboards showing only user-specific contributions.
  - Profile management for pen names and security updates.
- **Auto-Documentation:** - Fully interactive Swagger/OpenAPI documentation for easy frontend integration.

## 📦 Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/PrajwalRBhat/Sirsi_Sambhrama_Backend.git](https://github.com/PrajwalRBhat/Sirsi_Sambhrama_Backend.git)
   cd Sirsi_Sambhrama_Backend
Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

```bash
pip install -r requirements.txt
Set up environment variables:
Create a .env file in the root:

Code snippet
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
JWT_SECRET=your_secure_random_secret
MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_16_digit_app_password
ADMIN_INVITE_CODE=Sirsi@2026
Start Development Server:

```bash
uvicorn main:app --reload