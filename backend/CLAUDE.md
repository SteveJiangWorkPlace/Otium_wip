# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup and Initialization

### Environment Setup
```bash
# Create and activate virtual environment (recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your actual API keys and configuration
```

### Database Initialization
```bash
# Create data directory
mkdir -p data

# Initialize database tables
python -c "from models.database import init_database; init_database()"

# Ensure admin user exists (uses ADMIN_USERNAME/ADMIN_PASSWORD from .env)
python -c "from models.database import ensure_admin_user_exists; ensure_admin_user_exists()"
```

## Common Commands

### Development Server
```bash
# Start the FastAPI development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production server (using gunicorn with uvicorn workers)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Code Quality Tools
```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Lint with ruff
ruff check --fix .

# Type checking with mypy
mypy .
```

### Database Operations
```bash
# Initialize database tables (SQLAlchemy models)
python -c "from models.database import init_database; init_database()"

# Alembic Migration Commands
alembic upgrade head        # Apply all pending migrations
alembic current             # Show current migration revision
alembic history             # Show migration history
alembic revision --autogenerate -m "description"  # Create new migration
alembic downgrade -1        # Rollback last migration

# Database Maintenance
python scripts/migrate_to_database.py     # Migrate from JSON to SQL database
python scripts/test_migration.py          # Test database migration
python scripts/rollback_migration.py      # Rollback database migration

# User Management
python -c "from models.database import ensure_admin_user_exists; ensure_admin_user_exists()"
```

**Migration Notes**:
- Alembic configuration: `alembic.ini` with dynamic database URL from `config.get_database_url()`
- Migration scripts location: `migrations/versions/`
- Existing migration: `ecd2cc2e9e99_add_email_field_to_users_table.py` adds email field to users table
- Render pre-deploy script automatically runs `alembic upgrade head`

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py -v

# Run tests with coverage
pytest --cov=.
```

### Scripts
```bash
# Code Quality and Testing
python scripts/fix_code_quality.py        # Auto-fix code quality issues (black, isort, ruff)
python scripts/run_quality_checks.py      # Run all quality checks without fixing
python scripts/run_system_test.py         # Comprehensive system tests
python scripts/final_system_test.py       # Final system test suite

# Database Operations
python scripts/migrate_to_database.py     # Migrate from JSON to database
python scripts/test_migration.py          # Test database migration
python scripts/rollback_migration.py      # Rollback database migration

# Development Utilities
python scripts/print_routes.py            # Print all API routes
python scripts/install_dependencies.py    # Install dependencies
python scripts/verify_final_config.py     # Verify final configuration
```

### Windows编码兼容性
**重要**: 所有Python脚本都设计为Windows兼容，并遵循以下编码规范：

1. **避免Unicode符号**: 脚本输出中避免使用✓✗⚠等Unicode符号，改用：
   - `[成功]` 替代 ✓
   - `[失败]` 替代 ✗
   - `[警告]` 替代 ⚠
   - `[错误]` 替代 ❌

2. **编码处理**: 脚本强制设置UTF-8编码：
   - 设置系统环境变量: `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1`
   - 捕获输出时指定编码: `encoding="utf-8", errors="replace"`
   - 安全打印: 使用try-catch处理UnicodeEncodeError

3. **路径处理**: 使用`os.path`进行跨平台路径操作，避免硬编码路径分隔符

4. **日志输出**: 使用`logging`模块而非`print()`进行结构化日志记录

5. **示例脚本**: `scripts/run_quality_checks.py` 展示了完整的Windows兼容性实现

## Architecture Overview

### Technology Stack
- **Framework**: FastAPI with async support
- **Database**: SQLAlchemy ORM with SQLite (development) / PostgreSQL (production) support
- **AI Integration**: Google Gemini API for text processing and chat
- **Authentication**: JWT tokens with role-based access (user/admin)
- **Email Service**: Resend API only (SMTP support has been removed)
- **Rate Limiting**: Custom rate limiter with per-user quotas
- **Caching**: In-memory cache for API responses

### Key Directories and Files
- `main.py` - Main FastAPI application with all route definitions
- `config.py` - Centralized configuration management with environment variables
- `models/database.py` - SQLAlchemy models (User, UserUsage, TranslationRecord) and database utilities
- `api_services.py` - Gemini API integration for text processing, translation, and chat
- `user_services/user_service.py` - User authentication, registration, and management
- `services/` - Email and verification services
- `schemas.py` - Pydantic models for request/response validation
- `utils.py` - CacheManager, RateLimiter, TextValidator utilities
- `prompts.py` - Prompt templates for AI interactions

### Database Schema
- **users** - User accounts with authentication and quotas
- **user_usage** - Daily usage tracking for translations and AI detection
- **translation_records** - Detailed log of user operations

### API Structure
- `/api/login` - User authentication with JWT issuance
- `/api/register/*` - Email verification and user registration
- `/api/text/check` - Text error checking and translation
- `/api/text/translate-stream` - Stream translation with SSE
- `/api/text/refine` - English text refinement with directives
- `/api/text/detect-ai` - AI content detection using GPTZero
- `/api/chat` - AI chat conversation endpoint
- `/api/admin/*` - Admin-only user management endpoints
- `/api/health` - Health check endpoint

### Environment Variables
Key environment variables (see `.env.example` for full list):
- `GEMINI_API_KEY` - Google Gemini API key for text processing
- `GPTZERO_API_KEY` - GPTZero API key for AI detection
- `SECRET_KEY` / `JWT_SECRET_KEY` - JWT signing secret
- `DATABASE_TYPE` - "sqlite" or "postgresql"
- `DATABASE_URL` - PostgreSQL connection string (for production)
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` - Admin credentials
- `RESEND_API_KEY` - Email service API key
- `CORS_ORIGINS` - Comma-separated list of allowed origins

### Configuration Management
- Settings are loaded from environment variables with defaults
- Config class in `config.py` validates security settings and warns about defaults
- Environment detection (development/production) with Render platform support
- Feature flags for enabling/disabling specific functionalities

### User Management System
- Two-tier user system: admin users (environment variables) and regular users (database)
- Email verification required for registration
- Password reset with secure tokens
- Daily usage limits for translations and AI detection
- Usage tracking with reset logic

### AI Integration Patterns
- Gemini API calls with fallback models (gemini-2.5-flash primary, gemini-2.5-pro fallback)
- Prompt caching with performance monitoring
- Stream processing for real-time responses
- Text validation and sanitization before AI processing
- API key flexibility: environment variables or request headers

### Error Handling
- Centralized error handling via `@api_error_handler` decorator
- Structured error responses with error codes and details
- Graceful degradation when external services are unavailable
- Comprehensive logging at appropriate levels

### Development Notes
- Code formatting uses black with 100-character line length
- Import sorting follows black compatibility profile
- Type hints are encouraged but not strictly required
- Tests use pytest with markers (slow, integration, unit, api, auth, text, admin)
- Database migrations use Alembic (when configured) with fallback schema updates

## Deployment

### Deployment Architecture
- **Frontend**: Netlify (static hosting) with automatic deployments from GitHub
- **Backend**: Render (cloud service) with Python runtime
- **Architecture**: User → Netlify (frontend) → Render (backend API) → External services (Gemini AI, GPTZero)

### Frontend Deployment (Netlify)
1. Connect GitHub repository to Netlify
2. Build command: `cd frontend && npm run build`
3. Publish directory: `frontend/build`
4. Environment variable: `REACT_APP_API_BASE_URL` pointing to Render backend

### Backend Deployment (Render)
1. Create Web Service on Render with Python environment
2. Build command: `pip install -r backend/requirements.txt`
3. Start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Free tier limitations: Service sleeps after 15 minutes of inactivity, 750 hours monthly limit

### Environment Variables for Production
Key production environment variables (configure in Render dashboard):
```
# API Keys
GEMINI_API_KEY=your-gemini-api-key
GPTZERO_API_KEY=your-gptzero-api-key

# JWT Configuration
JWT_SECRET_KEY=your-strong-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
CORS_ORIGINS=https://your-netlify-app.netlify.app,http://localhost:3000

# Email Service Configuration (see Email Service section below)
EMAIL_PROVIDER=resend  # Only Resend API is supported
RESEND_API_KEY=your-resend-api-key
RESEND_FROM=your-verified-email@domain.com  # or onboarding@resend.dev for testing

# Database Configuration (for production)
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host:port/database
```

### Render-Specific Notes
- **Free tier limitations**: Service sleeps after inactivity, takes seconds to wake up
- **Ephemeral filesystem**: Not suitable for JSON file storage, use database instead
- **Health checks**: Render requires health endpoint, provided at `/api/health`
- **Automatic deployments**: Connected to GitHub for auto-deploy on push

### Docker Deployment
The project includes a Dockerfile for containerized deployment:

```dockerfile
# Dockerfile for Otium Backend on Render
# Uses Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Key features:
# - Non-root user (otiumuser) for security
# - Health check endpoint monitoring
# - Gunicorn with uvicorn workers for production
# - PostgreSQL client tools included

# Build and run:
docker build -t otium-backend .
docker run -p 8000:8000 -e PORT=8000 otium-backend
```

**Production CMD**: Uses gunicorn with 4 uvicorn workers, 120-second timeout
**Health check**: Monitors `/api/health` endpoint every 30 seconds
**Security**: Runs as non-root user (uid 1000) with proper permissions

### Render Blueprint Configuration
The project includes `render.yaml` for Infrastructure-as-Code deployment:

```yaml
# Key services defined:
# 1. Web service: otium-backend (Python 3.11)
# 2. PostgreSQL database: otium-database (PostgreSQL 16)

# Deployment features:
# - Automatic environment variable configuration
# - Database connection string injection
# - Pre-deploy script for database migrations
# - Health check path configuration
```

**Blueprint deployment**: Render can deploy entire stack (backend + database) from single YAML file
**Pre-deploy script**: Runs Alembic database migrations before deployment
**Auto-generated secrets**: JWT_SECRET_KEY and ADMIN_PASSWORD can be auto-generated
**Manual configuration required**: GEMINI_API_KEY, GPTZERO_API_KEY, RESEND_API_KEY must be set in Render dashboard

### Database Configuration for Production
- **Render PostgreSQL**: Free PostgreSQL add-on available
- **External alternatives**: Supabase, Neon, Railway
- **Migration script**: `python scripts/migrate_json_to_database.py` to migrate from JSON to database

### Security Deployment Checklist
- [ ] Change default admin password
- [ ] Use strong JWT secret key
- [ ] Enable HTTPS (auto-provided by Netlify and Render)
- [ ] Configure CORS origins appropriately
- [ ] Set up API rate limiting
- [ ] Implement database backups

## Email Service Configuration

### Available Email Providers
**Resend API Only**: HTTP API-based, more reliable in cloud environments. This is the only supported email provider.

**重要**: SMTP支持（包括SendGrid、QQ Mail等）已从代码库中完全移除：
- `config.py` 中 `EMAIL_PROVIDER` 硬编码为 "resend"
- `email_service.py` 虽然仍包含SMTP相关代码，但初始化时仅支持Resend API
- 所有环境变量配置仅针对Resend API

### Resend Configuration (Recommended)
```
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM=your-verified-email@domain.com  # or onboarding@resend.dev for testing
```



### Testing Email Configuration
- Check Render logs for email sending success/failure messages
- Test via API: `POST /api/register/send-verification` with test email
- Verify Resend API configuration and billing status

### Common Email Issues and Solutions
- **Resend API authentication failure**: Verify RESEND_API_KEY is valid and has proper permissions
- **Resend from address not verified**: Ensure RESEND_FROM is a verified email address in Resend dashboard
- **Resend API rate limits**: Check billing status and API rate limits in Resend dashboard
- **Emails going to spam**: Configure SPF/DKIM/DMARC records for your domain if using custom domain

## Troubleshooting

### Common Deployment Issues
1. **CORS errors**: Verify `CORS_ORIGINS` includes frontend domain
2. **Database connection failures**: Check `DATABASE_URL` format and network access
3. **Slow response after idle**: Render free tier service sleeps, takes seconds to wake up
4. **API key limits**: Verify Gemini/GPTZero API keys and quotas
5. **Email sending failures**: See Email Service Configuration section

### Development Environment Issues
- **Backend dependency errors**: Ensure Python 3.9+, virtual environment activated
- **Frontend npm errors**: Node.js 18+, clear cache, check network
- **API call errors**: Check backend service running at `http://localhost:8000/docs`

### Quick Start Scripts
- **Backend**: `backend/start_backend.bat` (Windows) or `backend/start_backend.ps1` (PowerShell)
- **Frontend**: `frontend/start_frontend.bat` (Windows) or `frontend/start_frontend.ps1` (PowerShell)

### Default Admin Credentials
- Username: `admin`
- Password: `admin123` (change in production!)

### API Rate Limits (Defaults)
- Regular users: 50 API calls per hour
- Admin users: 200 API calls per hour
- Adjustable in `UserLimitManager`

### Security Best Practices
1. Never commit API keys or secrets to version control
2. Use environment variables for all sensitive configuration
3. Implement strong password policies
4. Regularly update dependencies
5. Conduct security scans and code reviews