FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Assuming the app runs with uvicorn or similar based on main_http.py
# Adjust the command if it's a different entrypoint
CMD ["python", "main_http.py"]
