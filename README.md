# 👔 AI Wardrobe Studio

A modern, full-stack personal wardrobe management and outfit creation platform built with **FastAPI (Python)** on the backend and **React (Vite)** on the frontend.

---

## 🌟 Features

- **🔒 User Authentication:** Secure registration and JWT-based authentication with password hashing (Argon2).
- **👕 Wardrobe Management:** Add, filter, search, view, and delete clothing pieces (categorized into Upper, Lower, Shoes, Accessories).
- **📸 Media Uploads:** Direct image file upload support for wardrobe pieces served statically over `/media/`.
- **✨ Outfit Builder:** Interactive outfit builder tool to mix & match closet pieces, name your look, add descriptions, and mark favorites.
- **📱 Responsive UI:** Clean, modern studio aesthetic with desktop sidebar, mobile drawer navigation, and warm visual theme.

---

## 🛠️ Tech Stack

### **Backend**
- **Framework:** FastAPI (Python 3.13+)
- **ORM:** SQLAlchemy 2.0 (Async Engine)
- **Database:** SQLite (with `aiosqlite`) / PostgreSQL support
- **Migrations:** Alembic
- **Security:** PyJWT & Argon2 (`pwdlib`)
- **Package Manager:** `uv`

### **Frontend**
- **Framework:** React 18 (Vite 6)
- **Routing:** React Router v7
- **Icons:** Lucide React
- **Styling:** Custom CSS with CSS variables & responsive layout

---

## 📁 Project Structure

```text
AI-Wardrobe/
├── backend/
│   ├── main.py               # Uvicorn server launcher (http://127.0.0.1:8000)
│   ├── pyproject.toml        # Python dependencies
│   ├── alembic.ini           # Database migration configuration
│   ├── media/                # Directory for uploaded clothing images
│   ├── migrations/           # Alembic database migration scripts
│   └── app/
│       ├── app.py            # FastAPI application setup, CORS & routes
│       ├── core/             # JWT auth dependencies, security & settings
│       ├── db/               # Async database connection & sessions
│       ├── models/           # SQLAlchemy ORM models (User, ClothingItem, Outfit, OutfitItem)
│       ├── routes/           # FastAPI API endpoints (/auth, /user, /clothing-items, /outfits)
│       ├── schemas/          # Pydantic request & response validation schemas
│       ├── services/         # Business logic layer & file storage handlers
│       └── utils/            # Helper utilities
│
└── frontend/
    ├── package.json          # Node.js dependencies & scripts
    ├── index.html            # Vite HTML template
    └── src/
        ├── main.jsx          # React app entry point
        ├── App.jsx           # Application routes & layout wrapper
        ├── auth.jsx          # AuthContext provider (JWT & user session)
        ├── api.js            # API request helper client
        ├── styles.css        # Studio design system & CSS variables
        ├── components/       # Reusable components (Layout, Sidebar, Cards, UI)
        └── pages/            # Page views (Home, Wardrobe, Outfits, Builder, Auth)
```

---

## 🚀 Getting Started

### **Prerequisites**
- **Python:** 3.11+ (Python 3.13 recommended)
- **Node.js:** 18+ and `npm`

---

### **1. Backend Setup**

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment (or use `uv`):
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   # Or using uv:
   uv sync
   ```

4. Configure environment variables (create `.env` in `backend/`):
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./sql_app.db
   SECRET_KEY=your-super-secret-jwt-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the FastAPI backend server:
   ```bash
   python main.py
   ```
   *The backend will run at **http://127.0.0.1:8000**. Interactive API documentation is available at **http://127.0.0.1:8000/docs**.*

---

### **2. Frontend Setup**

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend will run at **http://127.0.0.1:5502** (or the port assigned by Vite).*

---

## 📡 API Endpoint Overview

| Module | Method | Endpoint | Description | Auth Required |
|---|---|---|---|---|
| **Auth** | `POST` | `/auth/login` | Authenticate user & return JWT token | No |
| **User** | `POST` | `/user/` | Register a new user | No |
| **User** | `GET` | `/user/me` | Fetch logged-in user profile | **Yes** |
| **Clothing** | `GET` | `/clothing-items/` | List user wardrobe items | **Yes** |
| **Clothing** | `POST` | `/clothing-items/` | Add new clothing piece (with optional image) | **Yes** |
| **Clothing** | `GET` | `/clothing-items/{id}` | View single clothing item details | **Yes** |
| **Clothing** | `PUT` | `/clothing-items/{id}` | Update clothing item | **Yes** |
| **Clothing** | `DELETE` | `/clothing-items/{id}` | Delete clothing item & image file | **Yes** |
| **Outfits** | `GET` | `/outfits/` | List user outfits | **Yes** |
| **Outfits** | `POST` | `/outfits/` | Create new outfit | **Yes** |
| **Outfits** | `GET` | `/outfits/{id}` | View single outfit details | **Yes** |
| **Outfits** | `PUT` | `/outfits/{id}` | Update outfit (toggle favorite / edit pieces) | **Yes** |
| **Outfits** | `DELETE` | `/outfits/{id}` | Delete outfit | **Yes** |

---

## 📜 License

This project is open-source and available under the MIT License.
