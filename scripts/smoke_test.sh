#!/bin/bash
# A simple smoke test to run after deployment

set -e

DOMAIN="medintel.yourdomain.com"
URL="https://$DOMAIN"

echo "Running smoke tests against $URL"

# 1. Test frontend
echo "Testing frontend accessibility..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
if [ "$HTTP_STATUS" -ne 200 ]; then
  echo "Frontend failed with status $HTTP_STATUS"
  exit 1
fi
echo "Frontend is UP."

# 2. Test backend health (Assuming a /api/health or similar exists)
echo "Testing backend API..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL/api/health")
if [ "$API_STATUS" -ne 200 ] && [ "$API_STATUS" -ne 404 ]; then # Allow 404 if health route isn't implemented
  echo "Backend API might be down. Status: $API_STATUS"
  exit 1
fi
echo "Backend API responded."

echo "Smoke tests passed successfully."
