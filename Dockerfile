# Use an official Debian image as the base
FROM debian:bookworm-slim

# Set the working directory inside the container
WORKDIR /app

# Update package lists and install all necessary packages
# Add 'netbase' here to provide the /etc/protocols file
RUN apt-get update && \
    apt-get install -y python3 python3-pip wakeonlan python3-flask netbase --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy the application file into the container
COPY app.py .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python3", "app.py"]
