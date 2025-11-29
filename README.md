# NATO Opportunities Website v2

A website to inform companies interested in doing work with NATO about all things NATO.

## 🎯 MVP Features

- **Landing Page**: Explains the site's purpose and value proposition
- **Opportunities Page**: Displays current (live) NATO opportunities from ACT IFIB
- **Automated Scraper**: Backend function that automatically checks for new opportunities and removes closed ones
- **Roadmap Page**: Users can vote on the next feature to implement

## 🏗️ Architecture

### Frontend
- **Framework**: Next.js 16 with TypeScript
- **Styling**: Tailwind CSS v4
- **Deployment**: Vercel (future)

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Testing**: pytest
- **Deployment**: Render (future)

### Scraper
- **Focus**: ACT IFIB opportunities scraper

## 📁 Project Structure

```
nato_website_2/
├── frontend/              # Next.js frontend application
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React components
│   ├── lib/              # Utilities and API client
│   └── public/           # Static assets
├── backend/              # FastAPI backend application
│   ├── app/              # FastAPI application files
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── database/         # Database configuration
│   ├── scraper/          # ACT IFIB opportunities scraper
│   └── api/              # API route handlers
├── tests/                # Test files
│   ├── backend/
│   └── frontend/
├── docs/                 # Documentation
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL (running locally or remote)

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env with your PostgreSQL connection string

# Run database migrations
alembic upgrade head

# Start the server
python -m uvicorn app.main:app --reload
```

Backend will run on http://localhost:8000
API docs available at http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
cp ../.env.example .env.local
# Edit .env.local with your configuration
npm run dev
```

Visit http://localhost:3000

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📝 Development

This is a rebuild from scratch, building feature by feature with testing along the way.

## 📄 License

MIT License

