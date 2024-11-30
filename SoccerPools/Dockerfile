FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Copy the wait script and make it executable
COPY wait_for_db.sh /app/wait_for_db.sh
RUN chmod +x /app/wait_for_db.sh

# RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["/app/wait_for_db.sh", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "90", "SoccerPools.wsgi:application"]