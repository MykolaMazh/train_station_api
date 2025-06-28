# 🚆 Train Station API

A Django REST Framework API for managing train stations, searching journeys, and booking tickets.

---

## 📦 Features

- 🔍 Search for train journeys  
- 🎟 Book tickets and manage orders  
- 👤 Register, log in, and manage user profiles  
- 🔐 JWT authentication  
- 📄 Interactive API documentation with Swagger & ReDoc  
- ⚙️ Admin dashboard for data management  

---

## 🚀 Tech Stack

- Python 3.11+  
- Django 4.x  
- Django REST Framework  
- PostgreSQL (via `DATABASE_URL`)  
- drf-spectacular for API docs  
- Render.com for deployment  

---

## ⚙️ Local Setup

### 1. Clone the project

\```
git clone https://github.com/yourusername/train-station-api.git
cd train-station-api
\```

### 2. Create and activate a virtual environment

\```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\```

### 3. Install dependencies

\```
pip install -r requirements.txt
\```

### 4. Create a `.env` file

Create a `.env` file in the root directory:

\```
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgres://user:password@localhost:5432/dbname
ALLOWED_HOSTS=127.0.0.1,localhost
\```

### 5. Run migrations

\```
python manage.py migrate
\```

### 6. Create a superuser (optional)

\```
python manage.py createsuperuser
\```

### 7. Run the server

\```
python manage.py runserver
\```

---

## 🔑 Authentication

This project uses **JWT authentication** with [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/).

### Auth Endpoints

| Method | URL                          | Description        |
|--------|------------------------------|--------------------|
| POST   | `/api/v1/user/register/`     | Register user      |
| POST   | `/api/v1/user/login/`        | Obtain token       |
| POST   | `/api/token/refresh/`        | Refresh token      |
| GET    | `/api/v1/user/me/`           | User profile       |

---

## 📬 API Endpoints

Example endpoints:

| Method | Endpoint                                | Description               |
|--------|------------------------------------------|---------------------------|
| GET    | `/api/v1/train_station/stations/`       | List all stations         |
| POST   | `/api/v1/train_station/orders/`         | Book a ticket             |
| GET    | `/api/v1/train_station/search-journeys/`| Search available journeys |
| GET    | `/api/v1/train_station/find-seats/`     | Check ticket availability |

---

## 📄 API Documentation

- Swagger UI: `/api/doc/swagger/`  
- ReDoc: `/api/doc/redoc/`  

---

## 🚀 Deployment (Render)

1. Push your project to GitHub  
2. Connect the repo to [Render.com](https://render.com)  
3. Set the build and start commands:

**Build command:**
\```
./build.sh
\```

**Start command:**
\```
gunicorn train_station_api.wsgi:application --workers 1 --threads 10
\```

4. Set environment variables in the Render dashboard:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `ALLOWED_HOSTS`

---

## 🧪 Run Tests

\```
python manage.py test
\```

---

## 📜 License

MIT License. See `LICENSE` for details.

---

## 👤 Author

**Your Name**  
GitHub: [@yourusername](https://github.com/yourusername)  
Email: you@example.com
