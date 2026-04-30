# AI Job Hunting Agent - Project Plan

## 1. PROJECT OVERVIEW

**Objective**: Build an intelligent AI agent that autonomously searches for job opportunities and startup companies, then applies or reaches out to them based on user preferences.

**Target Audience**: Job seekers interested in early-stage startups

**Core Value Proposition**: Automate the job search and application process across multiple platforms (Y Combinator, LinkedIn) with intelligent filtering and multi-channel outreach (application forms, email, LinkedIn messaging).

---

## 2. CORE FEATURES

### 2.1 Job Search & Filtering
- **Search Engines**:
  - Y Combinator Job Board (API/Web Scraping)
  - LinkedIn Jobs (LinkedIn API or web scraping)
  
- **Filtering Criteria**:
  - Keywords/technologies (Python, Node.js, React, etc.)
  - Location (remote, on-site, hybrid)
  - Job type (Full-time, Part-time, Contract)
  - Salary range
  - Company stage (Series A, B, Pre-seed, etc.)
  - Industry/sector

- **User Preferences**:
  - Store user profile (skills, experience, preferences)
  - Matching threshold (relevance score)
  - Geographic preferences

### 2.2 Company Discovery
- **Search Sources**:
  - Y Combinator Company Directory
  - LinkedIn Company Profiles
  
- **Information Extraction**:
  - Company name, stage, funding info
  - Founder/Co-founder details
  - Contact information (email, LinkedIn)
  - Industry/sector
  - Company size and growth metrics

### 2.3 Application & Outreach Mechanisms
- **Job Applications**:
  - Fill and submit application forms (using AI + form automation)
  - Track submitted applications
  - Store application status and responses

- **Email Outreach**:
  - Send personalized emails to founders/co-founders
  - Email templates with user information
  - Track email opens and responses (optional)

- **LinkedIn Messaging**:
  - Send connection requests + messages to founders/co-founders
  - Personalized message templates
  - Track message interactions

- **Multi-language Support** (optional):
  - Tailor outreach messages based on company location

### 2.4 AI Intelligence Layer
- **Job Matching Algorithm**:
  - NLP-based job description analysis
  - Relevance scoring (0-100)
  - Skills gap analysis

- **Personalization Engine**:
  - Generate tailored cover letters/messages
  - Context-aware outreach (mention company info, founder)
  - Intelligent response handling

---

## 3. TECHNICAL ARCHITECTURE

### 3.1 Frontend
- **Framework**: React + Vite (already initialized)
- **Features**:
  - User dashboard (profile, preferences, settings)
  - Job search interface
  - Application tracking (status, responses)
  - Analytics/reports (success rate, interviews, etc.)
  - Settings panel (API keys, preferences)

### 3.2 Backend
- **Framework**: Django (already initialized)
- **Database**: PostgreSQL or SQLite (currently using SQLite)
- **API Structure**: REST API with endpoints for:
  - User management & authentication
  - Job search & filtering
  - Company discovery
  - Application management
  - Outreach tracking
  - Settings management

### 3.3 External Integrations
- **Data Sources**:
  - Y Combinator API (if available) or web scraper
  - LinkedIn API (Jobs API, Recruiter API)
  - Job board scraping (Beautiful Soup, Selenium)

- **Communication Channels**:
  - Email service (SMTP, SendGrid, AWS SES)
  - LinkedIn API (messaging)
  - Browser automation (Selenium, Playwright) for form filling

- **AI/LLM Services**:
  - OpenAI (ChatGPT) / Claude API for:
    - Job matching analysis
    - Cover letter generation
    - Email/message personalization

### 3.4 Web Scraping & Data Collection
- **Tools**:
  - BeautifulSoup (parsing HTML)
  - Scrapy (large-scale scraping)
  - Selenium/Playwright (browser automation, form filling)
  - Requests-HTML (quick scraping)

### 3.5 Task Scheduling
- **Celery** + Redis/RabbitMQ for background tasks:
  - Periodic job searches
  - Application submissions
  - Email sending
  - LinkedIn messaging
  - Data updates

---

## 4. DATA MODELS & DATABASE SCHEMA

### 4.1 Core Entities

```
USER
├── id (PK)
├── email
├── password
├── first_name, last_name
├── profile_bio
├── skills (JSON)
├── experience_level (junior, mid, senior)
├── preferred_locations (JSON)
├── job_preferences (JSON)
├── created_at, updated_at

JOB
├── id (PK)
├── title
├── description
├── company_id (FK)
├── location
├── job_type (full-time, part-time, etc.)
├── salary_min, salary_max
├── posted_date
├── source (y_combinator, linkedin, etc.)
├── source_url
├── required_skills (JSON)
├── created_at

COMPANY
├── id (PK)
├── name
├── description
├── industry
├── stage (pre-seed, seed, series-a, etc.)
├── funding_amount
├── employee_count
├── website
├── source (y_combinator, linkedin)
├── source_id
├── created_at

FOUNDER
├── id (PK)
├── company_id (FK)
├── name
├── email
├── linkedin_url
├── title (founder, co-founder)

APPLICATION
├── id (PK)
├── user_id (FK)
├── job_id (FK)
├── application_date
├── status (submitted, rejected, accepted, interview)
├── application_method (form, email, linkedin)
├── response_received (bool)
├── response_date
├── response_text
├── notes

OUTREACH
├── id (PK)
├── user_id (FK)
├── founder_id (FK)
├── company_id (FK)
├── outreach_type (email, linkedin_message, linkedin_request)
├── message_content
├── sent_date
├── status (pending, sent, delivered, opened, replied)
├── response_received (bool)
├── response_date
├── response_text

USER_PREFERENCES
├── id (PK)
├── user_id (FK)
├── auto_apply (bool)
├── search_frequency (daily, weekly, etc.)
├── outreach_enabled (bool)
├── email_api_key (encrypted)
├── linkedin_credentials (encrypted)
├── openai_api_key (encrypted)
├── created_at

JOB_MATCH_LOG
├── id (PK)
├── user_id (FK)
├── job_id (FK)
├── match_score
├── matched_at
├── applied (bool)
```

---

## 5. TECHNOLOGY STACK

### Backend
- **Python 3.9+**
- **Django 4.x+** (REST Framework)
- **PostgreSQL** (or SQLite for dev)
- **Celery** (task scheduling)
- **Redis** (caching, message broker)

### Frontend
- **React 18+**
- **Vite** (build tool)
- **Tailwind CSS** (styling)
- **Axios** (API calls)
- **React Query** (data fetching)

### External Libraries
- **BeautifulSoup4** (web scraping)
- **Scrapy** (large-scale scraping)
- **Selenium** or **Playwright** (browser automation)
- **Requests** (HTTP requests)
- **Paramiko** (SSH for secure connections)
- **python-dotenv** (environment variables)
- **cryptography** (encrypt API keys)
- **OpenAI/Anthropic SDK** (LLM integration)

### DevOps
- **Docker** (containerization)
- **Docker Compose** (multi-container setup)
- **GitHub Actions** (CI/CD)

---

## 6. WORKFLOW & USER FLOW

### 6.1 User Registration & Setup
1. User signs up → creates account
2. Provides profile information (skills, experience, preferences)
3. Sets job preferences (technologies, location, salary range)
4. Configures outreach preferences (auto-apply, email, LinkedIn messaging)
5. Stores API keys securely (OpenAI, email service, LinkedIn)

### 6.2 Job Search & Match Workflow
1. **Trigger**: User initiates search or scheduled job runs
2. **Search**: Query Y Combinator & LinkedIn for matching jobs
3. **Filter**: Apply user preferences and filters
4. **Score**: AI analyzes job vs user profile, generates match score
5. **Store**: Save matched jobs to database
6. **Display**: Show results to user on dashboard
7. **Decide**: User decides to apply or skip

### 6.3 Application & Outreach Workflow
1. **Job Application**:
   - Detect application form on job posting
   - Auto-fill form with user data (name, email, etc.)
   - Generate AI-tailored cover letter
   - Submit application
   - Track status

2. **Founder/Co-founder Outreach**:
   - Extract founder info from company
   - Generate personalized message using AI
   - Send via email or LinkedIn
   - Track delivery and responses

### 6.4 Response Management
1. Receive email/LinkedIn responses
2. Flag for user review
3. Log interactions
4. Generate follow-up reminders

---

## 7. API ENDPOINTS (REST)

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### User Management
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/user/preferences` - Get user preferences
- `PUT /api/user/preferences` - Update preferences
- `POST /api/user/api-keys` - Store encrypted API keys

### Jobs
- `GET /api/jobs` - Get matched jobs (with filters)
- `GET /api/jobs/:id` - Get job details
- `POST /api/jobs/search` - Trigger manual job search
- `DELETE /api/jobs/:id` - Delete job

### Companies
- `GET /api/companies` - Get companies
- `GET /api/companies/:id` - Get company details
- `GET /api/companies/:id/founders` - Get founders info

### Applications
- `POST /api/applications` - Submit application
- `GET /api/applications` - Get user applications
- `GET /api/applications/:id` - Get application details
- `PUT /api/applications/:id` - Update application status

### Outreach
- `POST /api/outreach/email` - Send email to founder
- `POST /api/outreach/linkedin` - Send LinkedIn message
- `GET /api/outreach` - Get outreach history
- `PUT /api/outreach/:id/status` - Update outreach status

### Analytics
- `GET /api/analytics/dashboard` - Get dashboard stats
- `GET /api/analytics/success-rate` - Application success metrics
- `GET /api/analytics/job-trends` - Job market trends

---

## 8. SECURITY CONSIDERATIONS

- **Authentication**: JWT tokens
- **Encryption**: Encrypt API keys and credentials in database
- **Rate Limiting**: Prevent abuse of external APIs
- **CORS**: Configure properly for frontend
- **Data Privacy**: GDPR compliance
- **Secure Storage**: Use environment variables for secrets
- **Input Validation**: Sanitize all user inputs
- **HTTPS**: Enforce HTTPS in production

---

## 9. IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1-2)
- Set up Django backend structure
- Create database models
- Implement user authentication
- Set up API endpoints (basic CRUD)
- Frontend: Dashboard scaffold

### Phase 2: Data Collection (Week 3-4)
- Implement Y Combinator scraper
- Implement LinkedIn job search integration
- Store jobs in database
- Build job display on frontend

### Phase 3: AI Matching & Applications (Week 5-6)
- Integrate OpenAI/Claude API
- Build job matching algorithm
- Implement application form auto-fill
- Build application tracking

### Phase 4: Outreach System (Week 7-8)
- Implement email sending (SMTP/SendGrid)
- LinkedIn API integration for messaging
- Build founder/co-founder discovery
- Outreach tracking

### Phase 5: Task Scheduling & Automation (Week 9-10)
- Set up Celery + Redis
- Implement periodic job searches
- Automated application submissions
- Automated outreach

### Phase 6: Analytics & Polish (Week 11-12)
- Build analytics dashboard
- Performance optimization
- Error handling & logging
- Testing & bug fixes

---

## 10. CHALLENGES & SOLUTIONS

| Challenge | Solution |
|-----------|----------|
| LinkedIn Rate Limiting | Use authorized API keys, implement request queueing |
| Form Automation Complexity | Use Playwright/Selenium for JavaScript-heavy forms |
| API Key Management | Encrypt keys, use environment variables, rotate periodically |
| Email Deliverability | Use reputable email service (SendGrid), monitor bounce rates |
| LLM Cost (OpenAI) | Cache responses, batch requests, consider cheaper alternatives |
| Data Quality | Validate scraped data, remove duplicates, verify emails |
| Legal/ToS Issues | Check platform ToS, respect robots.txt, implement delays |
| User Privacy | GDPR compliance, secure credential storage, audit logging |

---

## 11. SUCCESS METRICS

- Number of jobs matched per user
- Application-to-response conversion rate
- Average response time from companies
- Interview rate
- Job offer rate
- User satisfaction score
- System uptime
- Data accuracy rate

---

## 12. FUTURE ENHANCEMENTS

- Mobile app (React Native)
- Browser extension for manual job browsing
- Interview preparation AI coach
- Salary negotiation assistant
- Resume optimization engine
- Multi-language support
- Webhook integrations
- Slack/Discord notifications
- Integration with more job boards (Indeed, AngelList, etc.)
- Machine learning model for better matching

---

## 13. REQUIREMENTS CHECKLIST

### Backend Requirements
- [ ] Django setup with REST framework
- [ ] Database models designed and migrated
- [ ] User authentication (JWT)
- [ ] API endpoints documented
- [ ] Logging system configured
- [ ] Error handling standardized

### Frontend Requirements
- [ ] React + Vite setup (done)
- [ ] Routing configured
- [ ] Authentication flow UI
- [ ] Dashboard UI
- [ ] Job search & filter UI
- [ ] Application tracking UI
- [ ] Settings/preferences UI

### External Integrations
- [ ] Y Combinator scraper/API
- [ ] LinkedIn API credentials
- [ ] OpenAI/Claude API setup
- [ ] Email service (SMTP/SendGrid)
- [ ] Redis setup
- [ ] Celery configuration

### Infrastructure
- [ ] Docker setup (partially done)
- [ ] Docker Compose configuration
- [ ] Environment variables setup
- [ ] Database initialization
- [ ] Caching setup

### Testing
- [ ] Unit tests for backend
- [ ] API integration tests
- [ ] Frontend component tests
- [ ] End-to-end tests

---

## 14. GETTING STARTED

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL (optional, can use SQLite for dev)
- Docker (optional)
- API keys: OpenAI, LinkedIn, Email service

### Quick Start
1. Clone repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Install Node dependencies: `cd frontend && npm install`
4. Set up `.env` file with API keys
5. Run migrations: `python manage.py migrate`
6. Start backend: `python manage.py runserver`
7. Start frontend: `cd frontend && npm run dev`

---

## 15. FOLDER STRUCTURE (Target)

```
jobHuntingAgent/
├── backend/
│   ├── jobhunt/               # Main Django app
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── ...
│   ├── accounts/              # User management
│   ├── jobs/                  # Job management
│   ├── companies/             # Company management
│   ├── applications/          # Application tracking
│   ├── outreach/              # Email/LinkedIn outreach
│   ├── integrations/          # External API integrations
│   ├── scraper/               # Web scraping logic
│   ├── ai/                    # AI/LLM logic
│   ├── tasks/                 # Celery tasks
│   ├── utils/                 # Utility functions
│   ├── tests/
│   ├── manage.py
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   ├── hooks/             # Custom hooks
│   │   ├── context/           # React context
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── ...
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
└── PROJECT_PLAN.md (this file)
```

---

## NOTES

- This plan is flexible and can be adjusted based on requirements
- Prioritize features based on MVP (Minimum Viable Product)
- Start with Y Combinator jobs/companies before expanding
- Consider legal/ethical implications of automation
- Test thoroughly before production deployment
