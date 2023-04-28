#!/bin/bash

# Exit with nonzero exit code if anything fails
set -eo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

KEYCLOAK_DEV_DOCKER_NAME=keycloak-dev
KEYCLOAK_DOCKER_TAG=20.0.5-0

if [[ -z $CI ]] && [[ -z $KEYCLOAK_ADMIN_PASSWORD ]]; then
  # Use Github Actions' env variables if not in CI or env already set
  eval $(yq '.jobs.test.env.[] | "export " + key + "=" + .' ../.github/workflows/test.yml)
fi

if ! docker ps -a --format '{{.Names}}' | grep -q "$KEYCLOAK_DEV_DOCKER_NAME"; then
  echo "Starting Keycloak docker service: $KEYCLOAK_DOCKER_TAG"
  docker run \
    --rm \
    --name "$KEYCLOAK_DEV_DOCKER_NAME" \
    -p "$KEYCLOAK_HOST:$KEYCLOAK_PORT:$KEYCLOAK_PORT" \
    -e "KEYCLOAK_ADMIN=$KEYCLOAK_ADMIN_USER" \
    -e "KEYCLOAK_ADMIN_PASSWORD=$KEYCLOAK_ADMIN_PASSWORD" \
    -d \
    "quay.io/keycloak/keycloak:$KEYCLOAK_DOCKER_TAG" \
    start-dev
else
  echo "Keycloak Docker service already running"
fi

KEYCLOAK_URL=http://$KEYCLOAK_HOST:$KEYCLOAK_PORT
echo "Waiting for Keycloak to launch on $KEYCLOAK_URL..."
# Abort after 90 seconds to avoid blocking (-m --> max time)
timeout --foreground 90 bash -c -- "\
  while ! curl -s -f -o /dev/null -m 2 \"$KEYCLOAK_URL/realms/master\"; do \
    echo 'Waiting...'; sleep 2 & wait; \
  done"

if (($(curl -s -o /dev/null -w "%{http_code}" "$KEYCLOAK_URL/realms/$KEYCLOAK_REALM") != 200)); then
  echo "Importing debug Keycloak setup"
  # Get an access token
  KEYCLOAK_TOKEN_RESPONSE=$(curl -s \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -d "username=$KEYCLOAK_ADMIN_USER" \
    -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
    "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token")
  KEYCLOAK_TOKEN=$(echo "$KEYCLOAK_TOKEN_RESPONSE" | jq -r .access_token)

  # Combine the realm and user config and send it to the Keycloak server
  HTTP_CODE=$(curl -X POST --data-binary "@realm-export.json" \
      -s -o /dev/null -w "%{http_code}" \
      -H "Content-Type: application/json" \
      -H "Authorization: bearer $KEYCLOAK_TOKEN" \
      "$KEYCLOAK_URL/admin/realms")
  if ((HTTP_CODE < 200 || HTTP_CODE >= 300)); then
    echo "Failed to import the $KEYCLOAK_REALM realm ($HTTP_CODE)"
    exit 1
  fi
  unset KEYCLOAK_TOKEN
else
  echo "Realm '$KEYCLOAK_REALM' already imported into Keycloak"
fi

poetry run test_site/manage.py migrate
if [[ "$1" == "coverage" ]]; then
  poetry run coverage run test_site/manage.py test test_app --failfast
  poetry run coverage report --rcfile=.coveragerc --data-file=.coverage
  poetry run coverage html --rcfile=.coveragerc --data-file=.coverage
else
  poetry run test_site/manage.py test test_app
fi