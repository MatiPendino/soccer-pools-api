# Soccer Pools API

This is the backend for the Soccer Pools project, built using Django and Django Rest Framework (DRF). The project consists of a picking game where users predict the outcomes of all matches in a league and earn points based on their predictions:

- **3 points:** Exact result prediction
- **1 point:** Correct winner prediction
- **0 points:** Incorrect prediction

Users can create groups (called **tournaments**) to compete with their friends.

## Project Status

This project is currently in its early development stage and has not yet reached its first official version.

## Features

- Predict match outcomes and earn points based on accuracy
- Rankings based on League and Stage
- Create and join tournaments to compete with friends
- Coin rewards system with a prize redemption shop
- Push notifications via Firebase Cloud Messaging
- Social Google OAuth authentication
- Asynchronous task processing with Celery and Redis
- Built with Django 5.2 and Django Rest Framework

## Architecture

### Django Apps

| App | Purpose |
|-----|---------|
| `app_user` | Custom user model, coins, referral system |
| `league` | Leagues, rounds, teams (integrates with API Football) |
| `bet` | User predictions (`BetLeague`, `BetRound` models) |
| `match` | Match data and user predictions with points |
| `tournament` | User groups for friend competitions |
| `notification` | Firebase Cloud Messaging push notifications |
| `prize` | Coin redemption shop |
| `payment` | Payment processing |

### Docker Services

| Service | Description |
|---------|-------------|
| `web` | Django app served with Gunicorn |
| `db` | PostgreSQL 14 |
| `redis` | Redis 6 (Celery broker and caching) |
| `celery` | Celery worker for async tasks |
| `celery-beat` | Celery scheduler for periodic tasks |

### External Integrations

- **API Football** — Match data source
- **Firebase** — Push notifications
- **SendGrid** — Transactional email
- **AWS S3** — File storage
- **Sentry** — Error tracking (production)

## Requirements

Ensure you have the following tools installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Installation and Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/MatiPendino/soccer-pools-api.git
   cd soccer-pools-api/SoccerPools
   ```

2. Create a `.env` file in the `SoccerPools/` directory (same level as `Dockerfile` and `docker-compose.yml`) with the required environment variables:

   ```bash
   SECRET_KEY=your_secret_key
   IS_PRODUCTION_ENV=False

   # Database
   DB_NAME=soccer_pools_db
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password

   # API Football
   API_FOOTBALL_KEY=your_api_football_key

   # Firebase (push notifications)
   FIREBASE_PROJECT_ID=your_firebase_project_id
   GOOGLE_APPLICATION_CREDENTIALS=soccerpools-firebase-adminsdk.json

   # AWS S3 (file storage)
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   AWS_STORAGE_BUCKET_NAME=your_bucket_name

   # SendGrid (email)
   SENDGRID_API_KEY=your_sendgrid_key
   ```

3. Build and start the Docker containers:

   ```bash
   docker-compose up --build
   ```

4. Create a superuser to access the admin panel:

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

The API will be accessible at: http://localhost:8000

## Running Tests

Run the full test suite:

```bash
docker-compose exec web python manage.py test apps
```

Run tests for a specific app:

```bash
docker-compose exec web python manage.py test apps.bet.tests
```

Run a specific test class:

```bash
docker-compose exec web python manage.py test apps.bet.tests.BetRoundResultsTest
```

## Useful Commands

```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Make new migrations
docker-compose exec web python manage.py makemigrations

# Open Django shell
docker-compose exec web python manage.py shell

# Create test players for a league (development)
docker-compose exec web python manage.py create_testing_players "League Name" 10
```

## API Documentation

Once the server is running, the API documentation is available at:

- **ReDoc:** http://localhost:8000/api/schema/redoc/
- **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/

## Frontend

This API is designed to work with the [React Native / Expo mobile app](https://github.com/MatiPendino/soccer-pools-mobile).

## Contributing

1. Fork the repository
2. Create a new branch: `git checkout -b feature-name`
3. Make your changes and commit: `git commit -m 'Add new feature'`
4. Push to your branch: `git push origin feature-name`
5. Open a Pull Request

## License

This project is licensed under the MIT License.
