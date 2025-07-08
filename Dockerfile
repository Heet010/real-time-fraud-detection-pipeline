# Dockerfile

FROM python:3.12-slim

WORKDIR /app

# 1. Copy only the API deps list
COPY requirements_api.txt .

# 2. Install those
RUN pip install --no-cache-dir -r requirements_api.txt

# 3. Copy rest of your code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "serve_model:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
