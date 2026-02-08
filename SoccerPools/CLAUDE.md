# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Soccer Pools API - A Django REST Framework backend for a soccer/football prediction game. Users predict match outcomes and earn points:
- 3 points: Exact score prediction
- 1 point: Correct winner prediction
- 0 points: Incorrect prediction

Users can create tournaments (groups) to compete with friends.

## Development Commands

```bash
# Build and start all services
docker-compose up --build

# Run tests
docker-compose exec web python manage.py test apps

# Run a single test file
docker-compose exec web python manage.py test apps.bet.tests

# Run a specific test class
docker-compose exec web python manage.py test apps.bet.tests.BetRoundResultsTest

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Make migrations
docker-compose exec web python manage.py makemigrations

# Create test players for a league (for development/testing)
docker-compose exec web python manage.py create_testing_players "League Name" 10

# Django shell
docker-compose exec web python manage.py shell
```

## Architecture

### Settings Structure
- `SoccerPools/settings/base.py` - Shared settings
- `SoccerPools/settings/local.py` - Local development (DEBUG=True, Celery eager mode)
- `SoccerPools/settings/production.py` - Production (DEBUG=False, SSL, Sentry)

Environment determined by `IS_PRODUCTION_ENV` variable via `utils.get_settings_env()`.

### Django Apps (in `apps/`)

| App | Purpose |
|-----|---------|
| `app_user` | Custom user model (`AppUser`), coins, referral system |
| `league` | Leagues, rounds, teams. Integrates with API Football |
| `bet` | User predictions - `BetLeague`, `BetRound` models |
| `match` | Match data and `MatchResult` (user predictions with points) |
| `tournament` | User groups for friend competitions |
| `notification` | Firebase Cloud Messaging push notifications |
| `prize` | Coin redemption shop |
| `base` | Abstract `BaseModel` with `state` (soft delete), `creation_date`, `updating_date` |
| `api` | Main API routing |

### Key Model Relationships
```
AppUser -> BetLeague -> BetRound -> MatchResult
              |            |
           League       Round -> Match
```

### State Patterns
All models inherit from `BaseModel` with `state=True` for active records (soft delete pattern).

Round states: `NOT_STARTED_ROUND (0)`, `PENDING_ROUND (1)`, `FINALIZED_ROUND (2)`
League states: `NOT_STARTED_LEAGUE (0)`, `PENDING_LEAGUE (1)`, `FINALIZED_LEAGUE (2)`
Match states: `NOT_STARTED_MATCH`, `PENDING_MATCH`, `FINALIZED_MATCH`, `CANCELLED_MATCH`, `POSTPONED_MATCH`, `PREPLAYED_MATCH`

### Celery Tasks
Configured in `SoccerPools/celery.py` with Redis broker. Key scheduled tasks:
- `check_upcoming_rounds()` - Sets round to PENDING 20min before start
- `finalize_pending_rounds()` - Finalizes completed rounds, distributes coin prizes
- `check_finalized_leagues()` - Handles league completion logic
- Push notification tasks for round start (24h ahead) and finalization

### Testing
Uses `APITestCase` from DRF with factory-boy factories in each app's `factories.py`. Tests use `force_authenticate()` for auth.

### API Documentation
Available at `/api/schema/redoc/` and `/api/schema/swagger-ui/` (DEBUG mode only).

### Docker Services
- `web` - Django app with Gunicorn
- `db` - PostgreSQL 14
- `redis` - Redis 6 (Celery broker, caching)
- `celery` - Celery worker
- `celery-beat` - Celery scheduler (DatabaseScheduler)

### External Integrations
- **API Football** - Match data source (`API_FOOTBALL_KEY`)
- **Firebase** - Push notifications (`FIREBASE_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`)
- **SendGrid** - Email via django-anymail
- **AWS S3** - File storage via django-storages
- **Sentry** - Error tracking (production)
