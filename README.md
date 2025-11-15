# Ad Mint AI - AI Video Ad Generator

A full-stack web application that enables users to create professional-quality video advertisements from simple text prompts using advanced AI models and proven advertising frameworks.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Demo User](#demo-user)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

Ad Mint AI is a web application that leverages AI to automatically generate coherent, persuasive video content suitable for social media platforms like Instagram, TikTok, and YouTube. The system uses proven advertising frameworks (AIDA, PAS, FAB) to create engaging narratives.

## ✨ Features

- **User Authentication**: Secure JWT-based authentication with bcrypt password hashing
- **Demo User**: Quick access with pre-configured demo account
- **Protected Routes**: Role-based access control for authenticated users
- **Modern UI**: Responsive React frontend with Tailwind CSS
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation
- **Database**: SQLAlchemy ORM with support for SQLite and PostgreSQL

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Database**: SQLAlchemy 2.0+ (SQLite for development, PostgreSQL for production)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Server**: Uvicorn with auto-reload for development

### Frontend
- **Framework**: React 19+
- **Language**: TypeScript 5.9+
- **Build Tool**: Vite 5.4+
- **Styling**: Tailwind CSS 4+
- **State Management**: Zustand 5+
- **Routing**: React Router 7+
- **HTTP Client**: Axios 1.13+
- **Testing**: Vitest 1.6+

### Development Tools
- **Linting**: ESLint 9+
- **Testing**: Pytest 7+ (backend), Vitest (frontend)
- **API Documentation**: FastAPI automatic OpenAPI/Swagger docs

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: 3.9 or higher
- **Node.js**: 20.19+ or 22.12+ (required for Vite 5.x+)
- **npm**: Comes with Node.js
- **Git**: For cloning the repository

### Checking Your Versions

```bash
# Check Python version
python --version  # or python3 --version

# Check Node.js version
node --version

# Check npm version
npm --version
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ad-mint-ai.git
cd ad-mint-ai
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

#### Environment Configuration (Optional)

Create a `.env` file in the `backend` directory for custom configuration:

```bash
# backend/.env
DATABASE_URL=sqlite:///./ad_mint_ai.db
SECRET_KEY=your-secret-key-here
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=True
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

**Default values** (if `.env` not provided):
- `DATABASE_URL`: `sqlite:///./ad_mint_ai.db`
- `SECRET_KEY`: `change-me-in-production`
- `CORS_ALLOWED_ORIGINS`: `http://localhost:5173,http://localhost:3000`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: `10080` (7 days)

#### Initialize Database

```bash
# Create database tables
python -m app.db.init_db
```

#### Create Demo User

```bash
# Create demo user for testing
python create_demo_user.py
```

Expected output:
```
Demo user created successfully!
   Username: demo
   Password: demo1234
   Email: demo@ad-mint-ai.com
```

### 3. Frontend Setup

Open a new terminal window and navigate to the frontend directory:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

#### Environment Configuration (Optional)

Create a `.env` file in the `frontend` directory:

```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

**Default value**: `http://localhost:8000`

## 🏃 Running the Application

You need to run both the backend and frontend servers simultaneously.

### Terminal 1: Start Backend Server

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Start the FastAPI server
uvicorn app.main:app --reload
```

The backend will be running at:
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Terminal 2: Start Frontend Server

```bash
# Navigate to frontend directory
cd frontend

# Start the Vite dev server
npm run dev
```

The frontend will be running at:
- **Application**: http://localhost:5173

### Verify Everything is Running

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/api/health
   ```
   Expected response: `{"status":"healthy"}`

2. **Frontend**: Open http://localhost:5173 in your browser

## 👤 Demo User

A demo user is included for quick testing:

- **Username**: `demo`
- **Password**: `demo1234`
- **Email**: `demo@ad-mint-ai.com`

You can use the **"Login as Demo User"** button on the login page for instant access.

## 📁 Project Structure

```
ad-mint-ai/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/        # API route handlers
│   │   │   │   └── auth.py    # Authentication endpoints
│   │   │   └── deps.py        # Dependency injection
│   │   ├── core/
│   │   │   ├── config.py      # Configuration management
│   │   │   └── security.py    # Password hashing & JWT
│   │   ├── db/
│   │   │   ├── models/        # SQLAlchemy models
│   │   │   │   ├── user.py
│   │   │   │   └── generation.py
│   │   │   ├── base.py        # Database engine
│   │   │   ├── session.py     # Session management
│   │   │   └── init_db.py     # Database initialization
│   │   ├── schemas/           # Pydantic schemas
│   │   │   └── auth.py
│   │   └── main.py            # FastAPI application entry
│   ├── tests/                 # Backend tests
│   ├── requirements.txt       # Python dependencies
│   ├── create_demo_user.py    # Demo user creation script
│   └── venv/                  # Virtual environment
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Navbar.tsx
│   │   │   ├── ui/            # Reusable UI components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   └── ErrorMessage.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── routes/
│   │   │   ├── Auth/
│   │   │   │   ├── Login.tsx
│   │   │   │   └── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Gallery.tsx
│   │   │   └── Profile.tsx
│   │   ├── store/
│   │   │   └── authStore.ts   # Zustand authentication store
│   │   ├── lib/
│   │   │   ├── apiClient.ts   # Axios instance
│   │   │   ├── authService.ts # Auth API calls
│   │   │   ├── config.ts      # API endpoints
│   │   │   └── types/
│   │   ├── __tests__/         # Frontend tests
│   │   ├── App.tsx            # Main app component
│   │   ├── main.tsx           # Entry point
│   │   └── index.css          # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   ├── postcss.config.js      # PostCSS/Tailwind config
│   └── tsconfig.json
│
├── deployment/                # Deployment configuration
│   ├── deploy.sh              # Deployment script
│   ├── nginx.conf             # Nginx configuration
│   ├── fastapi.service        # Systemd service file
│   └── README.md              # Deployment guide
│
├── docs/                      # Documentation
│   ├── PRD.md                 # Product Requirements
│   ├── architecture.md        # System architecture
│   ├── epics.md               # User stories and epics
│   └── sprint-artifacts/      # Sprint documentation
│
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 📚 API Documentation

### Interactive API Documentation

Once the backend is running, you can access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info (requires auth)

#### Health Check

- `GET /api/health` - API health status

### Example API Requests

#### Register User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "test@example.com"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "demo1234"
  }'
```

#### Get Current User (with JWT token)

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## 🧪 Testing

### Backend Tests

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth_routes.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
# Navigate to frontend directory
cd frontend

# Run all tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test -- --watch
```

## 🚀 Deployment

For production deployment instructions, see the [Deployment README](deployment/README.md).

### Quick Deployment Overview

The application is designed to be deployed on AWS EC2 with:
- **Nginx** as reverse proxy
- **Systemd** for process management
- **PostgreSQL** for production database (optional)

### Automated Deployment

```bash
# Run deployment script (on EC2 instance)
sudo ./deployment/deploy.sh /var/www/ad-mint-ai
```

## 🔧 Troubleshooting

### Backend Issues

#### Port 8000 Already in Use

```bash
# Find and kill process using port 8000
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# On macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

#### Database Errors

```bash
# Recreate database
cd backend
rm ad_mint_ai.db  # Remove existing database
python -m app.db.init_db  # Recreate tables
python create_demo_user.py  # Recreate demo user
```

#### Virtual Environment Not Activating

Make sure you're in the `backend` directory and use the correct activation command for your OS.

### Frontend Issues

#### Port 5173 Already in Use

Vite will automatically try the next available port (5174, 5175, etc.)

#### Node.js Version Too Old

If you see an error about Node.js version:

```bash
# Check your Node.js version
node --version

# If < 20.19, upgrade Node.js
# Download from: https://nodejs.org/
# Or use nvm (Node Version Manager)
```

#### Tailwind CSS Not Working

```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install

# Restart dev server
npm run dev
```

#### Module Not Found Errors

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### CORS Errors

If you see CORS errors in the browser console:

1. Check that the backend is running
2. Verify `CORS_ALLOWED_ORIGINS` in backend `.env` includes your frontend URL
3. Restart the backend server

### Authentication Issues

#### 401 Unauthorized Errors

- Check that you're logged in
- Verify the JWT token is stored in localStorage
- Token might be expired (default: 7 days)

#### 422 Validation Errors

- Check password length (minimum 8 characters)
- Verify username format (alphanumeric with underscores only)
- Check all required fields are provided

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all new frontend code
- Write tests for new features
- Update documentation as needed
- Run linters before committing:
  ```bash
  # Backend
  cd backend
  pytest
  
  # Frontend
  cd frontend
  npm run lint
  npm run test
  ```

## 📄 License

This project is part of the Gauntlet AI development program.

## 📞 Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review the [API Documentation](#api-documentation)
- Check existing issues in the repository
- Contact the development team

## 🙏 Acknowledgments

- FastAPI for the excellent backend framework
- React and Vite teams for modern frontend tooling
- Tailwind CSS for utility-first styling
- OpenAI and Replicate for AI capabilities (future integration)

---

**Version**: 1.0  
**Last Updated**: November 15, 2025  
**Status**: Active Development

