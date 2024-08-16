#!/bin/sh

# Check if .env file exists and load environment variables
if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

KONG_ADMIN_URL="http://localhost:8001"
HOST="172.17.0.1"  # Replace with your desired host

# Wait for Kong to be ready
until $(curl --output /dev/null --silent --head --fail $KONG_ADMIN_URL); do
  printf '.'
  sleep 5
  echo "Waiting for Kong Gateway to be ready..."
done

# Function to create service, route, and enable JWT plugin
create_service_route_and_jwt() {
  service_name=$1
  port=$2
  enable_jwt=$3

  # Create the service
  curl -i -X POST $KONG_ADMIN_URL/services/ \
      --data "name=$service_name" \
      --data "url=http://$HOST:$port"

  # Create the route
  curl -i -X POST $KONG_ADMIN_URL/services/$service_name/routes \
      --data "paths[]=/${service_name}" \
      --data name=${service_name}-route \
      --data "strip_path=true"

  # Enable JWT plugin if specified
  if [ "$enable_jwt" = true ]; then
    curl -i -X POST $KONG_ADMIN_URL/services/$service_name/plugins \
        --data "name=jwt"
  fi
}

# Create services and routes, with JWT enabled for all except user-service
create_service_route_and_jwt "user-service" 8005 false
create_service_route_and_jwt "product-service" 8006 true
create_service_route_and_jwt "inventory-service" 8007 true
create_service_route_and_jwt "order-service" 8008 true
create_service_route_and_jwt "payment-service" 8009 true
create_service_route_and_jwt "notification-service" 8010 true

echo "Kong Gateway setup completed!"
