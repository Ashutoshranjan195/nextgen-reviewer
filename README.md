# ⚡ NextGen Code Reviewer

**24/7 Intelligent Code Review** — AI-powered code analysis with multi-language support, historical rule learning, and a premium dark-mode dashboard.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-LLM-black?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)

---

## Features

- 🔐 **Secure Authentication** — JWT-based login/register with bcrypt password hashing
- 🌍 **Multi-Language Support** — Python, JavaScript, TypeScript, Java, Go, Rust, C++, C#, Ruby, PHP
- 🤖 **AI-Powered Reviews** — Ollama LLM integration for intelligent code analysis
- 📊 **Quality Ratings** — 1–10 rating with categorized issues (formatting, performance, security, best-practice, optimization)
- 📋 **Review History** — Persistent submission history with timestamps and previews
- 📚 **Historical Rules** — Upload CSV files to teach the reviewer custom quality guidelines
- 📈 **Dashboard Analytics** — Total reviews, average rating, growth score, language breakdown
- 🎨 **Premium UI** — Glassmorphism dark theme with smooth animations
- 🐳 **Docker Ready** — One-command deployment with docker-compose

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Ollama** (for AI-powered reviews) — [Install Ollama](https://ollama.ai)

### 1. Clone and Setup

```bash
cd nextgen-reviewer/backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your settings (optional — defaults work for local dev)
```

### 3. Start Ollama (for AI reviews)

```bash
# In a separate terminal
ollama serve

# Pull a model (first time only)
ollama pull llama3
```

> **Note:** If Ollama is not running, the system automatically falls back to a rule-based reviewer.

### 4. Run the Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

---

## Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Pull the Ollama model (first time)
docker exec -it nextgen-reviewer-ollama-1 ollama pull llama3
```

The app will be available at **http://localhost:8000**.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/register` | ❌ | Create a new user account |
| `POST` | `/api/login` | ❌ | Authenticate and get JWT token |
| `POST` | `/api/submit` | ✅ | Submit code for AI review |
| `GET` | `/api/history` | ✅ | Get user's review history |
| `POST` | `/api/upload-csv` | ✅ | Upload CSV with quality rules |
| `GET` | `/api/rules` | ✅ | Get active review rules |
| `GET` | `/api/health` | ❌ | Health check |

### Example Usage

```bash
# Register
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "dev", "password": "mypassword"}'

# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "dev", "password": "mypassword"}'

# Submit code (use token from login response)
curl -X POST http://localhost:8000/api/submit \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello():\n  print(\"hi\")", "language": "python"}'
```

---

## CSV Rules Format

Upload a CSV file with these columns to add custom review rules:

```csv
id,type,description
1,formatting,Avoid single-character variable names — they hurt readability
2,performance,Cache repeated database lookups inside the request loop
3,security,Never interpolate raw user input directly into SQL queries
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Project Structure

```
nextgen-reviewer/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── config.py         # Settings from .env
│   │   ├── database.py       # Async SQLAlchemy setup
│   │   ├── models.py         # ORM models (User, Submission, Rule)
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── auth.py           # JWT + bcrypt utilities
│   │   ├── dependencies.py   # FastAPI dependencies
│   │   ├── reviewer.py       # Ollama LLM integration
│   │   └── routes/
│   │       ├── auth_routes.py
│   │       ├── review_routes.py
│   │       └── rules_routes.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── app.js, api.js, auth.js
│       ├── reviewer.js, history.js
│       ├── rules.js, dashboard.js
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./reviewer.db` | Database connection string |
| `JWT_SECRET` | `change-me-...` | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRE_MINUTES` | `60` | Token expiration time |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3` | Ollama model to use |
| `OLLAMA_TIMEOUT` | `120` | LLM request timeout (seconds) |
| `MAX_CODE_LENGTH` | `50000` | Max code submission length |

---

## License

MIT
