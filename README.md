# Country Currency & Exchange API
This project implements the Country Currency & Exchange API described in your task using Django + Django REST Framework and MySQL as persistence.


Features
- POST /countries/refresh -> fetch countries & exchange rates and cache them in the DB
- GET /countries -> list (filters: region, currency; sort: gdp_desc)
- GET /countries/<name> -> get single country by name
- DELETE /countries/<name> -> delete country record
- GET /status -> show total and last refresh timestamp
- GET /countries/image -> serve generated summary image (cache/summary.png)


Quick start
1. Copy `.env.example` to `.env` and edit values.
2. Create the database in MySQL (name = DB_NAME in .env).
3. `python -m venv venv && source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`
7. POST to `/countries/refresh` to populate.


Notes
- Uses a management command and a POST endpoint to trigger the refresh logic.
- Summary image saved to `cache/summary.png`.
- External API failures return 503 and do not modify DB.