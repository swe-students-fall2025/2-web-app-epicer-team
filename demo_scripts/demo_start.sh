#!/bin/bash
set -e

# === Load environment variables ===
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

CONTAINER_NAME="mongodb_dockerhub"
IMAGE_NAME="mongo:latest"
DB_NAME=${MONGO_DB:-grocery_app}

# === SUDO IN CASE ===
DOCKER_CMD="docker"
if ! groups $USER | grep -q "\bdocker\b"; then
  DOCKER_CMD="sudo docker"
fi

# === Check if container exists ===
if [ "$($DOCKER_CMD ps -aq -f name=^${CONTAINER_NAME}$)" ]; then
  if [ "$($DOCKER_CMD ps -q -f name=^${CONTAINER_NAME}$)" ]; then
    echo "MongoDB container '$CONTAINER_NAME' is already running."
  else
    echo "Starting existing MongoDB container..."
    $DOCKER_CMD start $CONTAINER_NAME
    echo "MongoDB is running!"
    echo "URI: mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$DB_NAME?authSource=admin"
  fi
else
  echo "'$CONTAINER_NAME' does not exist. Please run 'demo_setup.sh' first."
fi
