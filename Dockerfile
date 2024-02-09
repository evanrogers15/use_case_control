# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy the contents of the gns3_app directory into the container
COPY . /app/

# Expose port 8080 for Flask
EXPOSE 8080

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install SQLite and VIM
RUN apt-get update && apt-get install -y sqlite3 vim

# Setup SQLite
RUN python modules/setup/sqlite_setup.py

# Set the default command to run both Flask and Node.js
CMD ["bash", "-c", "python -m flask run -p 8080 --host=0.0.0.0"]
