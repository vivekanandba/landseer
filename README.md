# Landseer

**A comprehensive land search and evaluation system for Vellore, Tamil Nadu**

> *Land + Seer: One who sees and evaluates land with clarity*

---

## Overview

Landseer is a full-stack application designed to streamline the process of finding, evaluating, and purchasing agricultural and residential land in Vellore district. It combines property management, document verification, broker tracking, and intelligent matching to help make informed land purchasing decisions.

## Key Features

### 🏘️ Property Management
- Track properties across Vellore district (villages, taluks, survey numbers)
- Manage subdivisions and adjacent neighbor properties
- Rich notes with photos, videos, and observations
- Visit history and timeline tracking

### 👔 Broker Management
- Track brokers and their listings
- Record contact history and interactions
- Performance metrics and ratings
- Commission tracking

### 📄 Document Vault
- Store and organize Patta, FMB, EC, Sale Deeds
- OCR extraction of key fields (survey numbers, owner names, extents)
- Document verification checklists
- Expiry tracking for time-sensitive documents

### 🗺️ Survey Visualization
- Import survey vertices and generate KML files
- Interactive map view with property boundaries
- Auto-upload to Google My Maps
- Neighbor property mapping

### 🎯 Smart Matching
- Define your property requirements (size, location, budget, features)
- Auto-score properties against your preferences
- Deal-breaker detection
- Intelligent recommendations

### ⚖️ Comparison Tools
- Side-by-side property comparison
- Custom criteria weighting
- Investment analysis (ROI, appreciation estimates)
- Export comparison reports (PDF)

### 🔔 Automation
- Import existing data from OneDrive
- Document expiry reminders
- Price change alerts
- Follow-up notifications

---

## Technology Stack

### Backend
- **Python 3.11+** - FastAPI
- **PostgreSQL 15** - Database with PostGIS extension
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Celery + Redis** - Background tasks
- **Tesseract/Google Vision** - OCR

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Next.js** - React framework
- **TailwindCSS + shadcn/ui** - Styling
- **Google Maps API** - Map visualization

### Testing
- **pytest + Behave** - Backend testing (TDD/BDD)
- **Jest + React Testing Library** - Frontend unit tests
- **Cypress** - E2E testing

### Infrastructure
- **Docker + Docker Compose** - Containerization
- **GitHub Actions** - CI/CD
- **Nginx** - Reverse proxy

---

## Project Structure

```
landseer/
├── backend/                   # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   ├── schemas/          # Pydantic schemas
│   │   └── tests/            # Unit, integration, E2E tests
│   ├── features/             # BDD specifications (Gherkin)
│   └── alembic/              # Database migrations
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Next.js pages
│   │   ├── services/         # API client
│   │   └── hooks/            # Custom React hooks
│   └── cypress/              # E2E tests
├── data/                     # Data storage
│   ├── imports/              # OneDrive sync folder
│   ├── processed/            # Processed documents
│   ├── exports/              # Generated reports
│   └── kml/                  # KML files for Google Maps
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15 with PostGIS
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   cd /Users/Vivekanand.balakrishnan/per/landseer
   ```

2. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Database setup**
   ```bash
   createdb landseer
   psql -d landseer -c "CREATE EXTENSION postgis;"
   alembic upgrade head
   ```

4. **Frontend setup**
   ```bash
   cd frontend
   npm install
   ```

5. **Run development servers**
   ```bash
   # Backend (terminal 1)
   cd backend
   uvicorn app.main:app --reload

   # Frontend (terminal 2)
   cd frontend
   npm run dev
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Development Workflow

### Test-Driven Development (TDD)
```bash
# Write test first
cd backend
pytest tests/unit/test_property_model.py

# Implement feature to make test pass
# Run tests again
pytest

# Refactor
```

### Behavior-Driven Development (BDD)
```bash
# Write Gherkin specification
vim backend/features/property_management.feature

# Implement step definitions
vim backend/features/steps/property_steps.py

# Run BDD tests
behave
```

### Frontend Component Testing
```bash
cd frontend
npm test                    # Run Jest tests
npm run cypress:open        # Run Cypress E2E tests
```

---

## Key Workflows

### Import Existing Data from OneDrive
```bash
python scripts/import_onedrive.py \
  --source "/Users/Vivekanand.balakrishnan/Library/CloudStorage/OneDrive-Sanas.ai/Personal/Documents/TN Lands" \
  --target "./data/imports"
```

### Generate KML from Survey Vertices
```bash
python scripts/generate_kml.py \
  --survey-number "171-4D" \
  --vertices "12.786202,79.082576;12.786492,79.082490;..." \
  --output "./data/kml/171-4D.kml"
```

### Run OCR on Documents
```bash
python scripts/ocr_extract.py \
  --input "./data/imports/Thuthikadu/171-4-Patta.pdf" \
  --output "./data/processed/thuthikadu_171_4_patta.json"
```

---

## Testing

### Run All Tests
```bash
# Backend
cd backend
pytest                      # Unit + integration tests
behave                      # BDD tests
pytest --cov=app            # With coverage

# Frontend
cd frontend
npm test                    # Jest tests
npm run cypress:run         # E2E tests
```

### Test Coverage Goals
- Backend: 95%+ for models and services
- Frontend: 85%+ for components
- E2E: Critical user workflows covered

---

## API Documentation

Full API documentation is available at `/docs` when running the backend server.

Key endpoints:
- `GET /api/v1/properties` - List all properties
- `POST /api/v1/properties` - Create property
- `GET /api/v1/properties/{id}` - Get property details
- `POST /api/v1/properties/{id}/documents` - Upload document
- `GET /api/v1/brokers` - List brokers
- `POST /api/v1/comparisons` - Create property comparison

---

## Roadmap

### Phase 1: Foundation (Weeks 1-4) ✅ Current
- [x] Project setup with TDD/BDD
- [ ] Database models
- [ ] Core API endpoints
- [ ] OneDrive importer

### Phase 2: Document Intelligence (Weeks 5-8)
- [ ] OCR integration
- [ ] Document verification
- [ ] Neighbor tracking

### Phase 3: Intelligence & Matching (Weeks 9-12)
- [ ] Preference engine
- [ ] Scoring algorithm
- [ ] Smart recommendations

### Phase 4: Visualization (Weeks 13-16)
- [ ] KML generator migration
- [ ] Interactive maps
- [ ] Google My Maps integration

### Phase 5: Frontend (Weeks 17-20)
- [ ] React application
- [ ] Mobile PWA
- [ ] Comparison tools

---

## Contributing

This is a personal project for Vellore land search. Development follows:
- Test-Driven Development (TDD)
- Behavior-Driven Development (BDD)
- Clean code principles
- Comprehensive documentation

---

## License

Private project - All rights reserved

---

## Contact

For questions or feedback, please create an issue in the repository.

---

**Built with ❤️ for finding the perfect land in Vellore**
