# Setup Guide for NATO Website v2

This guide will help you set up the development environment for `nato_website_2`.

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL (running locally or remote)
- Git

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
cp ../.env.example .env
# Edit .env with your PostgreSQL connection string
# DATABASE_URL=postgresql://user:password@localhost:5432/nato_opportunities
```

### 4. Set Up Database

#### Option A: Using Alembic (Recommended)

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

#### Option B: Using init_db.py

```bash
python database/init_db.py
```

### 5. Run Backend

```bash
python -m uvicorn app.main:app --reload
```

Backend will run on http://localhost:8000
API docs available at http://localhost:8000/docs

### 6. Run Backend Tests

```bash
pytest
```

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Set Up Environment Variables

```bash
cp ../.env.example .env.local
# Edit .env.local - NEXT_PUBLIC_BACKEND_URL should point to your backend
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Run Frontend

```bash
npm run dev
```

Visit http://localhost:3000

## Database Setup (PostgreSQL)

### Create Database

```bash
# Using psql
psql -U postgres
CREATE DATABASE nato_opportunities;
\q

# Or using createdb
createdb nato_opportunities
```

### Update .env

Make sure your `DATABASE_URL` in `backend/.env` points to your PostgreSQL database:

```
DATABASE_URL=postgresql://username:password@localhost:5432/nato_opportunities
```

## Project Structure

```
nato_website_2/
├── backend/              # FastAPI backend
│   ├── app/             # FastAPI app
│   ├── core/            # Core configuration
│   ├── database/        # Database setup and migrations
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── repositories/    # Data access layer
│   ├── services/        # Business logic
│   ├── api/             # API routes
│   └── scraper/         # Scraper logic (future)
├── frontend/            # Next.js frontend
│   ├── app/            # Next.js App Router
│   ├── components/     # React components
│   └── lib/            # Utilities and API client
└── tests/              # Test files
```

## Next Steps

1. Verify backend health: http://localhost:8000/health
2. Check API docs: http://localhost:8000/docs
3. Verify frontend: http://localhost:3000
4. Run tests: `pytest` in backend directory

## Troubleshooting

### Backend Issues

- **Import errors**: Make sure virtual environment is activated
- **Database connection errors**: Check PostgreSQL is running and DATABASE_URL is correct
- **Migration errors**: Make sure database exists and user has permissions

### Frontend Issues

- **Cannot connect to backend**: Check NEXT_PUBLIC_BACKEND_URL in .env.local
- **Build errors**: Delete .next folder and node_modules, then reinstall

