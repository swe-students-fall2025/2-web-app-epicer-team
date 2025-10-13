#!/usr/bin/env bash
set -e

CONTAINER_NAME="mongodb_dockerhub"

# === SUDO IN CASE ===
DOCKER_CMD="docker"
if ! groups $USER | grep -q "\bdocker\b"; then
  DOCKER_CMD="sudo docker"
fi

if [ "$($DOCKER_CMD ps -q -f name=^${CONTAINER_NAME}$)" ]; then
  echo "Stopping MongoDB container..."
  $DOCKER_CMD stop $CONTAINER_NAME
else
  echo "MongoDB container '$CONTAINER_NAME' is not running."
fi
