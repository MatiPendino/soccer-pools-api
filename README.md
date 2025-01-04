# Soccer Pools API

This is the backend for the Soccer Pools project, built using Django and Django Rest Framework (DRF). The project consists of a picking game where users predict the outcomes of all matches in a league and earn points based on their predictions:

- **3 points:** Exact result prediction
- **1 point:** Correct winner prediction
- **0 points:** Incorrect prediction

Users can create groups (called **tournaments**) to compete with their friends.

## Project Status

This project is currently in its early development stage and has not yet reached its first official version.

## Features

- Predict match outcomes and score points based on accuracy
- Rankings based on League and Stage
- Create and join tournaments to compete with friends
- Social Google OAuth
- Built using Django and Django Rest Framework
- Docker and Docker Compose support for easy setup

## Requirements

Ensure you have the following tools installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Installation and Setup

Follow these steps to set up and run the project locally:

1. Clone the repository:

   ```bash
   git clone https://github.com/MatiPendino/soccer-pools-api.git
   cd soccer-pools-api
   
Create an .env file at the root of the project (same level as Dockerfile and docker-compose.yml) and specify the required environment variables:

```bash
  SECRET_KEY=your_secret_key
  POSTGRES_DB=soccer_pools_db
  POSTGRES_USER=your_db_user
  POSTGRES_PASSWORD=your_db_password
  SOCIAL_GOOGLE_OAUTH_ANDROID_CLIENT_ID=your_google_oauth_android_client_id
```

Build and start the Docker containers:

```bash
docker-compose up --build
```

Create a superuser (for accessing the admin panel):

```bash
docker-compose exec web python manage.py createsuperuser
```

The API should now be accessible at: http://localhost:8000

## Running Tests
You can run the test suite using the following command:

```bash
docker-compose exec web python manage.py test apps
```

## API Documentation
The API documentation can be accessed once the server is running at http://localhost:8000/api/schema/redoc

## Frontend
This API is designed to work with the [React Native / Expo mobile repository](https://github.com/MatiPendino/soccer-pools-mobile)

## Contributing
Fork the repository

Create a new branch (git checkout -b feature-name)

Make your changes and commit them (git commit -m 'Add new feature')

Push the changes to your branch (git push origin feature-name)

Create a Pull Request


## License
This project is licensed under the MIT License.
