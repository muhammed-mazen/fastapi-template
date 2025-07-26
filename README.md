# FastAPI Template

A lightweight and extensible **FastAPI** template designed for production-ready applications. This template includes:

- Optimized structure for scalability
- Pre-configured routing, middleware, and database setup
- Automated testing using **pytest**
- Alembic migrations for database schema management
- Prometheus for monitoring
- Middleware for performance and logging

##  Getting Started

### **1. Clone the Repository**

```sh
git clone https://gitlab.com/YOUR_USERNAME/YOUR_PROJECT.git
cd YOUR_PROJECT
```

### **2. Set Up Virtual Environment**

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

### **3. Install Dependencies**

```sh
pip install -r requirements.txt
```

### **4. Run the Application**

```sh
uvicorn main:app --reload
```

##  Project Structure

```
.
├── app/                # Core application logic
│   ├── routes/         # API routes
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   ├── schemas/        # Pydantic schemas
│   ├── config.py       # Configuration settings
│   ├── dependencies.py # Dependency injection
│   ├── __init__.py
│
├── tests/              # Unit and integration tests
├── migrations/         # Alembic migration scripts
├── .gitlab-ci.yml      # GitLab CI/CD pipeline
├── .env.example        # Environment variables template
├── main.py             # Application entry point
├── requirements.txt    # Project dependencies
└── README.md
```

##  Running Tests

```sh
pytest
```

##  Contributing

Feel free to open issues or submit pull requests for improvements.

---

## Author

**Muhammed Mazen Hafez**  
[mhmazen.com](https://mhmazen.com)  
[LinkedIn](https://www.linkedin.com/in/mhmazen) | [GitHub](https://github.com/muhammed-mazen)  
Email: mh.mazen@hotmail.com

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
