#!/usr/bin/env bash
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found! Please create one."
  exit 1
fi

# === CONFIGURATION ===
CONTAINER_NAME="mongodb_dockerhub"
IMAGE_NAME="mongo:latest"
DB_NAME=${MONGO_DB:-grocery_demo}
DEMO_DATA_DIR="./demo_scripts/demo_data"

# === SUDO IN CASE ===
DOCKER_CMD="docker"
if ! groups $USER | grep -q "\bdocker\b"; then
  DOCKER_CMD="sudo docker"
fi

# === STEP 1: Recreate container safely ===
if [ "$($DOCKER_CMD ps -aq -f name=$CONTAINER_NAME)" ]; then
  echo "Removing existing container $CONTAINER_NAME..."
  $DOCKER_CMD rm -f $CONTAINER_NAME
fi

echo "Starting MongoDB Docker container..."
$DOCKER_CMD run --name $CONTAINER_NAME \
    -p 27017:27017 \
    -e MONGO_INITDB_ROOT_USERNAME=$MONGO_USER \
    -e MONGO_INITDB_ROOT_PASSWORD=$MONGO_PASS \
    -d $IMAGE_NAME

# Wait for MongoDB to start
echo "Waiting for MongoDB to initialize..."
sleep 10

echo "Copying demo JSON files into the container..."
$DOCKER_CMD cp "$DEMO_DATA_DIR/." "$CONTAINER_NAME":/tmp/demo_data/

echo "Importing demo data into MongoDB..."
for file in $(ls $DEMO_DATA_DIR/*.json); do
  collection=$(basename "$file" .json)
  echo "Importing $collection.json into collection '$collection'..."
  $DOCKER_CMD exec -i $CONTAINER_NAME mongoimport \
      -d $DB_NAME \
      --authenticationDatabase admin \
      --collection $collection \
      --file /tmp/demo_data/$collection.json \
      --jsonArray \
      --username $MONGO_USER \
      --password $MONGO_PASS
done

echo ""
echo "MongoDB setup complete!"
echo "Database: $DB_NAME"
echo "User: $MONGO_USER"
echo "Password: $MONGO_PASS"
echo "Mongo running on: mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$DB_NAME?authSource=admin"
