# Train Station API

## Overview

The Train Station API is a Django REST Framework project designed to provide services for managing train station information, searching the journeys and book tickets. This API includes endpoints for registering users, obtaining authentication tokens.

## Installation

### 1. Clone the repository

Clone the project from GitHub:

```bash
git clone --branch develop --single-branch https://github.com/MykolaMazh/train_station_api.git
```

### 2. Set up your environment

Create a `.env` file in the root of your project to configure the database settings and secret key. 

#### Example `.env`(obligatory  for development) :

```bash
SECRET_KEY=your_secret_key

```
#### Example `.env`(obligatory  for production) :
```bash
SECRET_KEY=your_secret_key
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=your_db_host
DATABASE_PORT=your_db_port
DJANGO_SETTINGS_MODULE=train_station_api.settings.prod('for production, uses postgreSQL')
DJANGO_SETTINGS_MODULE=train_station_api.settings.dev('for development, uses SQlite')
```

### 3. Database setup

For development, use SQLite. For production, configure PostgreSQL according to your `.env` file.




### Documentation endpoints

- **Swagger UI**: `api/doc/swagger/`
- **ReDoc**: `api/doc/redoc/`



## Settings

Settings are split into two files: `dev.py` for development and `prod.py` for production.

- Development (`dev.py`): Uses SQLite.
- Production (`prod.py`): Uses PostgreSQL, configured via the `.env` file.

## Docker Setup 

Use the following Docker commands.

### 1. Build the Docker image

```bash
docker build train_station_api/ -t train_station_api
```

### 2. Run the Docker container

```bash
docker run --name train_station -p 8010:8000 train_station_api
```

### User Endpoints

- **Register User**: `POST /api/v1/user/register/`
- **Get Token**: `POST /api/v1/user/login/`
- **Obtain JWTToken**: `POST /api/token/`


### Main usage Endpoints

- **search journeys between stations**: `POST /api/v1/train_station/search-journeys/`
- **find available seat for the choosen journey**: `POST /api/v1/train_station/find-seats/`
- **book tickets**: `POST /api/v1/train_station/orders/`

Use `api/doc/swagger/` endpoint to get more endpoints documentation   

Visit `http://127.0.0.1:8000` to access the API.



## Additional Information

- The project uses **Django REST Framework** for building the API.
- The API documentation is auto-generated with **drf-spectacular**.
- The project uses **PostgreSQL** for production and **SQLite** for development.
