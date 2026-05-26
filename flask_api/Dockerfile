# 1. Use an official lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy just the requirements file first to take advantage of Docker caching
COPY requirements.txt .

# 4. Install dependencies directly into the container (no virtual env needed inside Docker)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code into the container
COPY . .

# 6. Expose the port Flask runs on
EXPOSE 5000

# 7. Command to run the application
CMD ["python", "app.py"]