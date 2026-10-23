FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY shop ./shop
COPY docker-entrypoint.sh .

ENV FLASK_APP=shop
EXPOSE 8000

ENTRYPOINT ["sh", "docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "shop:create_app()"]
