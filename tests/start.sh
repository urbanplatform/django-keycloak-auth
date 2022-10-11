#!/bin/bash

# Exit with nonzero exit code if anything fails
set -exo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

KEYCLOAK_URL=http://$KEYCLOAK_HOST:$KEYCLOAK_PORT
echo "Waiting for Keycloak to launch on $KEYCLOAK_URL..."
# Abort after 10 seconds to avoid blocking (-m --> max time)
while ! curl -s -f -o /dev/null -m 2 "$KEYCLOAK_URL/auth/realms/master"; do
  echo "Waiting..."
  sleep 2 &
  wait
done

echo "Importing debug Keycloak setup"
# Get an access token
KEYCLOAK_TOKEN_RESPONSE=$(curl -s \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=$KEYCLOAK_ADMIN_USER" \
  -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
  "$KEYCLOAK_URL/auth/realms/master/protocol/openid-connect/token")
echo "$KEYCLOAK_TOKEN_RESPONSE"
KEYCLOAK_TOKEN=$(echo "$KEYCLOAK_TOKEN_RESPONSE" | jq -r .access_token)
echo "$KEYCLOAK_TOKEN"
# Combine the realm and user config and send it to the Keycloak server
HTTP_CODE=$(curl -X POST --data-binary "@realm-export.json" \
    -s -o /dev/null -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -H "Authorization: bearer $KEYCLOAK_TOKEN" \
    "$KEYCLOAK_URL/auth/admin/realms")
if ((HTTP_CODE < 200 || HTTP_CODE >= 300)); then
  echo "Failed to import the $KEYCLOAK_REALM realm ($HTTP_CODE)"
  exit 1
fi
unset KEYCLOAK_TOKEN

poetry run test_site/manage.py test test_app