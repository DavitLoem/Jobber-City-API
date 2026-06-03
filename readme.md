# Form Login API

A FastAPI-based authentication API with MongoDB backend.

## Features

- User registration with password hashing (bcrypt)
- User login with JWT token authentication
- MongoDB database integration
- Environment-based configuration

## Prerequisites

- Python 3.8+
- MongoDB (local or remote)

To run this application, type following commands:

```bash
# for development
uvicorn main:app --reload --port=8000

# for production
uvicorn main:app --port=8000 --workers=4

# add admin user
python manage_db.py seed
# reset database (drop all collections)
python manage_db.py reset
# reset database and add admin user
python manage_db.py fresh

## Installation

1. Clone the repository and navigate to the project directory

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure environment variables in `.env`:
```
MONGO_USERNAME = your_username
MONGO_PASSWORD = your_password
MONGO_HOST = localhost
MONGO_PORT = 27017
```

## Running the Application

Start the development server:
```bash
python -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn | ASGI server |
| pymongo | MongoDB driver |
| python-dotenv | Environment variable management |
| bcrypt | Password hashing |
| PyJWT | JWT token handling |

## Project Structure

```
.
├── main.py              # FastAPI application entry point
├── .env                 # Environment configuration
├── requirements.txt     # Python dependencies
├── venv/src/           # Source code (auth module)
│   ├── config/mongo.py # Database configuration
│   ├── model/auth.py   # Data models
│   ├── services/auth.py # Business logic
│   └── controllers/auth.py # Route handlers
└── readme.md           # This file
```

## License

MIT# Jobber-City-API
