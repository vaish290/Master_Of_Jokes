# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Poetry (dependency management tool)
RUN pip install poetry

# Install dependencies from pyproject.toml (without dev dependencies)
RUN poetry install --no-dev

# Expose port 5000 to allow external access
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=app
ENV FLASK_ENV=development  

# Run the application using Flask's development server
CMD ["poetry", "run", "flask", "run", "--host=0.0.0.0"]