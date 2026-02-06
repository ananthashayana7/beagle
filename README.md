# 🐕 Beagle - Enterprise AI-Powered Data Analysis Platform

> Transform your data into actionable insights with natural language. Upload, analyze, and visualize in seconds.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-green.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109-teal.svg)

## 🎯 Overview

Beagle is an enterprise-grade data intelligence platform that enables business leaders to analyze complex datasets using natural language. Powered by Google Gemini AI, it combines conversational AI, automated code generation, and interactive visualizations in a secure, scalable architecture.

### Key Features

- **🤖 Natural Language Analysis** - Ask questions about your data in plain English
- **📊 Automated Visualizations** - Generate Plotly charts with AI recommendations
- **🐍 Sandboxed Code Execution** - Run Python securely with full data access
- **🔐 Enterprise Security** - JWT authentication, RBAC, rate limiting
- **📁 Multi-Format Support** - CSV, Excel, JSON, Parquet file processing
- **⚡ Real-Time Processing** - Stream responses and live visualizations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  (Dashboard, Workspace Chat, File Management, Settings)     │
├─────────────────────────────────────────────────────────────┤
│                     Nginx Reverse Proxy                     │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Backend                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │   Auth   │   Files  │   Chat   │ Execute  │   Viz    │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Security │ Rate Limit │ Sanitizer │ AI Service      │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│   PostgreSQL  │    Redis    │    MinIO    │    Gemini     │
│   (Database)  │   (Cache)   │  (Storage)  │     (AI)      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Google Gemini API key (optional, demo mode available)

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/beagle.git
cd beagle

# Copy environment template
cp .env.example .env

# Add your Gemini API key (optional)
echo "GEMINI_API_KEY=your-key-here" >> .env
```

### 2. Start with Docker

```bash
docker-compose up -d
```

Services will be available at:
- **Frontend**: http://localhost:80
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

### 3. Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
beagle/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes (auth, files, chat, execute, visualize)
│   │   ├── core/          # Security, rate limiting, sanitization
│   │   ├── models/        # SQLAlchemy database models
│   │   ├── schemas/       # Pydantic validation schemas
│   │   ├── services/      # Business logic (AI, file processing, etc.)
│   │   ├── config.py      # Configuration management
│   │   ├── database.py    # Database connection
│   │   └── main.py        # FastAPI application
│   ├── alembic/           # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── layouts/       # Page layouts
│   │   ├── pages/         # React pages
│   │   ├── stores/        # Zustand state management
│   │   ├── lib/           # API client, utilities
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔒 Security Features

| Feature | Implementation |
|---------|----------------|
| Authentication | JWT with access/refresh tokens |
| Password Storage | bcrypt hashing |
| Authorization | Role-based access control (Admin/Analyst/Viewer) |
| API Protection | Rate limiting per endpoint |
| Input Validation | Pydantic schemas + sanitization |
| Code Execution | Sandboxed Python with AST validation |
| File Handling | Type validation, size limits, secure storage |

## 🔧 API Endpoints

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Auth** | `POST /api/auth/register` | Create account |
| | `POST /api/auth/login` | Get access token |
| | `POST /api/auth/refresh` | Refresh token |
| **Files** | `POST /api/files/upload` | Upload data file |
| | `GET /api/files/{id}/preview` | Get data preview |
| | `GET /api/files/{id}/statistics` | Get column stats |
| **Chat** | `POST /api/conversations` | Create conversation |
| | `POST /api/conversations/{id}/messages` | Send message |
| **Execute** | `POST /api/execute` | Run Python code |
| **Visualize** | `POST /api/visualizations/generate` | Create chart |
| | `GET /api/visualizations/suggest/{file_id}` | AI suggestions |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

Built with ❤️ for enterprise data intelligence
