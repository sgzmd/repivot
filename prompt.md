# Role: Senior Python Data Engineer & Full-Stack Architect

## Context
Build a secure, mobile-optimized PWA (Progressive Web App) called "RePivot" designed to process financial XLS exports. The app allows users to upload or "Share-to-App" (via Android) an XLS file from Revolut as well as any other app, process the data using Pandas + optionally LLMs, and store monthly aggregates in a local database.

## Tech Stack Requirements
- **Backend:** Python 3.11+, FastAPI (for performance and async support).
- **Data Processing:** Pandas.
- **Database:** SQLite with SQLAlchemy ORM (for VPS/local portability).
- **Frontend:** Streamlit OR a lightweight FastAPI + Jinja2/Tailwind setup (must support PWA Manifest for Android Share Target).
- **Security:** Google OAuth2 (OpenID Connect) with a hardcoded `ALLOWED_USERS` list.
- **Deployment:** Dockerized for AWS (ECS/App Runner) or a generic VPS.

## 1. Functional Specifications
### A. Data Ingestion & Processing
- **Inputs:** Support `.xls`/`.xlsx` via file uploader and the Android "Web Share Target" API.
- **Filtering:** - Keep only rows where `Type == 'Card Payment'`.
    - Columns to extract: `Product`, `Started`, `DateCompleted`, `DateDescription`, `Amount`, `Fee`, `Currency`.
- **Transformation:** - Create a new column `TotalCost = Amount + Fee`.
    - Pivot the data by `Description` (from `DateDescription`).
    - Aggregate: `sum(TotalCost)`.
- **User Input:** On every upload, the app must prompt: "Who is this for?" (Options: [Eva, Sophie]).

### B. Persistence Layer
- **Schema:** - Table: `monthly_summaries` (Columns: person_name, month_year, description, total_amount, currency).
- **Granularity:** Monthly.
- **Logic:** If a report for the same `Month` and `Person` is uploaded again, overwrite existing records for that month (Upsert logic).

### C. Security
- **Auth:** Implement Google Social Login.
- **Authorization:** Only email addresses in the environment variable `ALLOWED_USERS` (comma-separated) can access the app. Redirect all others to a "403 Unauthorized" page.

Ensure app is protected against CSRF, XSS, and other common web vulnerabilities. All cookies are HttpOnly and Secure.

## 2. Technical Deliverables
1. **PWA Manifest:** A `manifest.json` including the `share_target` configuration to allow the app to appear in the Android "Share" menu for files.
2. **Backend Logic:** Clean, modular Python code with:
    - `processor.py`: Pandas logic.
    - `models.py`: SQLAlchemy schemas.
    - `auth.py`: Google OAuth middleware.
3. **Unit Tests:** Provide a PyTest suite for the Pandas transformation logic.
4. **Deployment:** A `Dockerfile` and `docker-compose.yml` optimized for a VPS.

## 3. Quality Constraints
- Use strict type hinting (`mypy` compatible).
- Implement structured logging.
- Ensure the UI (the "Pretty Report") uses a clean, mobile-responsive layout (e.g., Plotly charts for the pivot table).
- Handle edge cases: Missing columns in XLS, corrupted files, and expired OAuth tokens.

## 4. Execution Plan
Please provide the response in two parts:
1. **Architectural Overview:** Explain how the Android Share Target will communicate with the Python backend.
2. **Code Implementation:** The complete code for the application, following the directory structure of a professional Python project.
