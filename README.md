# Tambayi Nasarawa

**Development of a Hausa–English Bilingual FAQ Chatbot for Nasarawa State Government Services**

Tambayi Nasarawa is a Django 5 web application that helps residents find government-service information in English or Hausa. Answers come only from bilingual FAQs maintained by authorized administrators. If matching confidence is too low, the application records the question for editorial review instead of generating an answer.

## Main capabilities

- Bilingual chatbot with explicit language selection and conservative automatic detection
- Exact, keyword, partial, category, token-overlap and RapidFuzz matching
- Separate progressive-enhancement FAQ search page
- Session-owned conversations, history, feedback and clear-chat support
- Unanswered-question queue with ranked matching attempts and conversion to draft FAQ
- Django administration for categories, translations, keywords, sources and publishing
- Four roles: Super Administrator, FAQ Manager, Content Editor and Analytics Viewer
- Chart.js analytics for usage, language, categories, top FAQs and content gaps
- CSRF protection, throttling, security headers, redaction of common credentials and retention tooling
- PostgreSQL/Gunicorn/Nginx deployment configuration

## Architecture

```text
config/                    Django settings, URLs, WSGI and ASGI
apps/
  accounts/                Role and permission provisioning
  core/                    Shared security, text normalization and public pages
  faq/                     Bilingual FAQ models, admin, search and APIs
  chatbot/                 Conversations, matching, feedback and unanswered questions
  analytics/               Event capture, aggregation and reporting dashboard
templates/                 Django templates (Bootstrap 5)
static/css/                Government visual system
static/js/                 Vanilla JavaScript chat, search and charts
deploy/                    Gunicorn, Nginx and systemd examples
```

Business logic is in `services.py` modules. Views validate transport input and delegate to services.

## Local installation

### 1. Requirements

- Python 3.12+
- PostgreSQL 14+ for production (SQLite is an explicit development/test fallback)
- Optional Redis for shared production throttling/cache

### 2. Create an environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

For local SQLite development, keep `DB_ENGINE=sqlite`. For PostgreSQL:

```env
DB_ENGINE=postgresql
DB_NAME=nasarawa_chatbot
DB_USER=nasarawa_chatbot
DB_PASSWORD=a-strong-database-password
DB_HOST=127.0.0.1
DB_PORT=5432
```

Replace `DJANGO_SECRET_KEY` with a long random value. Review the official enquiry email/URL with the government content owner before deployment.

### 4. Create the schema and starter content

```bash
python manage.py migrate
python manage.py seed_faqs
python manage.py createsuperuser
python manage.py setup_roles
```

`seed_faqs` is idempotent. It creates the eight required categories and starter bilingual FAQs. Entries without confirmed operational details are visibly marked **Awaiting official confirmation**.

### 5. Run

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Administration is at `/admin/`; analytics is at `/dashboard/` for authorized users.

## Administrator roles

Create a staff user, then assign a role:

```bash
python manage.py setup_roles --username USERNAME --role "FAQ Manager"
```

| Role | Main access |
|---|---|
| Super Administrator | All project and user-management permissions |
| FAQ Manager | Categories, FAQs, publishing, unanswered review and summary analytics |
| Content Editor | Create/edit drafts and translations; cannot publish or delete |
| Analytics Viewer | Read-only analytics, conversations and unanswered-question counts |

Superusers retain Django’s unrestricted administration access.

## Adding a bilingual FAQ

1. Sign in at `/admin/` and open **Frequently asked questions**.
2. Select a category.
3. Enter English and Hausa questions and answers.
4. Add keyword arrays and alternative expressions as JSON lists, for example:
   `["scholarship", "bursary"]`.
5. Select the verification state.
6. For **Verified**, provide the official source URL and verification date.
7. Save as draft, review both translations, then publish with an account that has publishing permission.

Publishing validation blocks incomplete bilingual entries and verified entries without a source URL.

## Matching behavior

The matcher normalizes case, punctuation, Hausa `ƙ/ɗ/ɓ`, accented/unaccented spelling and common word variants. It evaluates:

- exact questions and alternative expressions;
- keyword phrases;
- partial containment;
- meaningful token overlap;
- RapidFuzz weighted and token-set similarity;
- category names; and
- a reduced-weight translated-question fallback.

`CHAT_MATCH_THRESHOLD` controls when an answer is reliable enough to return. `CHAT_SUGGESTION_THRESHOLD` controls related suggestions. A failed match creates an `UnansweredQuestion`; no generative fallback fabricates content.

## API

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/chat/message/` | Public session, CSRF + throttle |
| GET | `/api/chat/history/` | Current browser session only |
| POST | `/api/chat/feedback/` | Current browser session, CSRF |
| POST | `/api/chat/clear/` | Current browser session, CSRF |
| GET | `/api/faq/` | Public, published only |
| GET | `/api/faq/categories/` | Public, active only |
| GET | `/api/faq/search/?q=...` | Public + throttle |
| GET | `/api/analytics/?days=30` | Authenticated analytics permission |

Public POST endpoints require Django’s CSRF cookie and `X-CSRFToken` header. The included JavaScript handles this automatically.

## Testing and checks

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

The suite covers bilingual retrieval, fuzzy search, publishing validation, sessions, history, unanswered recording, feedback, CSRF, credential redaction, role restrictions and analytics permissions.

Before production, run Django’s deployment check using production environment values:

```bash
python manage.py check --deploy
```

## Privacy and data retention

- The UI warns users not to enter passwords, BVN, NIN, card PINs or banking details.
- Common labelled credentials/card-number patterns are redacted before persistence.
- FAQ search analytics store query length and result count, not raw query text.
- Conversations belong to an opaque Django session and are not accessible across sessions.
- Run the retention command daily (cron/systemd timer):

```bash
python manage.py purge_chat_data --days 90 --analytics-days 730
python manage.py purge_chat_data --dry-run
```

Choose retention periods with the government data-protection owner before launch.

## Production deployment

1. Set `DJANGO_DEBUG=False`, a strong secret, exact allowed hosts and trusted HTTPS origins.
2. Configure PostgreSQL and run `python manage.py migrate`.
3. Configure Redis with `CACHE_BACKEND=redis` and `REDIS_URL=...` when running multiple workers.
4. Run `python manage.py collectstatic --noinput`.
5. Copy and edit `deploy/nginx.conf`; install TLS certificates.
6. Copy and edit `deploy/tambayi-nasarawa.service`, then enable the service.
7. Start Gunicorn with `deploy/gunicorn.conf.py`.
8. Send console/file logs to the government logging platform. Set `SENTRY_DSN` for optional error monitoring; personally identifiable information is disabled.
9. Monitor `/health/` from the load balancer.

Example:

```bash
gunicorn config.wsgi:application --config deploy/gunicorn.conf.py
```

### Backups

Create encrypted, access-controlled PostgreSQL backups and test restoration regularly:

```bash
pg_dump --format=custom --file=nasarawa_chatbot_$(date +%F).dump nasarawa_chatbot
pg_restore --clean --if-exists --dbname=nasarawa_chatbot restored-backup.dump
```

### Deploying to Vercel

This project includes a Vercel Python function entry point in [`api/index.py`](api/index.py)
and routing in [`vercel.json`](vercel.json). Vercel deployments must use PostgreSQL;
SQLite files are ephemeral in serverless deployments.

1. Create a PostgreSQL database using a provider such as Neon, Supabase or
   Vercel Postgres.
2. Install and authenticate the Vercel CLI:

   ```bash
   npm install --global vercel
   vercel login
   ```

3. From the project root, run `vercel` and link the project when prompted.
4. Add these environment variables in the Vercel project settings for
   **Production** (replace the example values):

   ```env
   DJANGO_DEBUG=False
   DJANGO_SECRET_KEY=<long-random-secret>
   DJANGO_ALLOWED_HOSTS=<project>.vercel.app
   DJANGO_CSRF_TRUSTED_ORIGINS=https://<project>.vercel.app
   DATABASE_URL=postgresql://<user>:<password>@<host>/<database>?sslmode=require
   DJANGO_SECURE_SSL_REDIRECT=True
   DJANGO_SECURE_COOKIES=True
   ```

   Neon provides the `DATABASE_URL` value. Keep the connection string secret.
   The separate `DB_*` variables are also supported if you prefer them.
   Add the custom domain to both `DJANGO_ALLOWED_HOSTS` and
   `DJANGO_CSRF_TRUSTED_ORIGINS` if one is configured.
5. Deploy with `vercel --prod`.
   The Vercel build runs Django migrations automatically before collecting
   static files.
6. Create the first administrator against the production database from a
   machine with the production variables loaded:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py setup_roles
   ```

   Do not commit `.env` or database credentials. Vercel environment variables
   are the source of truth for deployment secrets.

Do not place backups in the web root. Define retention, off-site replication and restore testing with the infrastructure owner.

## Accuracy workflow

The seeded URLs were reviewed when the starter data was prepared, but government procedures can change. A responsible agency should review every answer, source, Hausa translation and confirmation date before public launch. Never publish a fee, deadline, address or eligibility rule without a current official source.
