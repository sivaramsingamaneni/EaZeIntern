# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
# We copy requirements.txt first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose port 10000
EXPOSE 10000

# Default command: Run the FastAPI app
# We use shell form to allow passing arguments if needed, but CMD is typically exec form.
# Using a list allows signals to pass correctly.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
