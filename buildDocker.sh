# Prompt for Docker Hub username
read -p "Enter your Docker username: " DOCKER_USERNAME

# Prompt for password securely (no echo)
read -s -p "Enter your Docker password: " DOCKER_PASSWORD
echo ""

# Log in to Docker non-interactively
echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USERNAME" --password-stdin

# Clear the password variable from memory
unset DOCKER_PASSWORD

echo "Docker login complete."

docker build -t chaconn3/bmgt435_service:alpha .
docker push chaconn3/bmgt435_service:alpha