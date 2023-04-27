#!/bin/bash

# Exit with nonzero exit code if anything fails
set -eo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

if [[ -z $CI ]] && [[ -z $KEYCLOAK_ADMIN_PASSWORD ]]; then
  # Use Github Actions' env variables if not in CI or env already set
  eval $(yq '.jobs.test.env.[] | "export " + key + "=" + .' ../.github/workflows/test.yml)
fi

KEYCLOAK_URL=http://$KEYCLOAK_HOST:$KEYCLOAK_PORT
if [[ $KEYCLOAK_LEGACY = true ]]; then
  KEYCLOAK_PATH="$KEYCLOAK_URL/auth"
  KEYCLOAK_LEGACY_TEXT="legacy"
else
  KEYCLOAK_PATH="$KEYCLOAK_URL"
  KEYCLOAK_LEGACY_TEXT="modern"
  export KEYCLOAK_BASE_PATH="/"
fi

echo "Waiting for $KEYCLOAK_LEGACY_TEXT Keycloak to launch on $KEYCLOAK_URL..."
# Abort after 10 seconds to avoid blocking (-m --> max time)
while ! curl -s -f -o /dev/null -m 2 "$KEYCLOAK_PATH/realms/master"; do
  echo "Waiting..."
  sleep 2 &
  wait
done

if (($(curl -s -o /dev/null -w "%{http_code}" "$KEYCLOAK_PATH/realms/$KEYCLOAK_REALM") != 200)); then
  echo "Importing debug Keycloak setup"
  # Get an access token
  KEYCLOAK_TOKEN_RESPONSE=$(curl -s \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -d "username=$KEYCLOAK_ADMIN_USER" \
    -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
    "$KEYCLOAK_PATH/realms/master/protocol/openid-connect/token")
  KEYCLOAK_TOKEN=$(echo "$KEYCLOAK_TOKEN_RESPONSE" | jq -r .access_token)

  # Get Keycloak server version to add the right config file
  KEYCLOAK_VERSION="$(curl -s \
    -H "Content-Type: application/json" \
    -H "Authorization: bearer $KEYCLOAK_TOKEN" \
    "$KEYCLOAK_PATH/admin/serverinfo" \
    | jq '.systemInfo.version')"
  echo "Keycloak version: $KEYCLOAK_VERSION"
  VERSION_MAJOR="$(echo "$KEYCLOAK_VERSION" | tr -d \" | cut -d . -f 1)"
  if [ "$VERSION_MAJOR" -le 14 ]; then
    REALM_FILE="realm-export-13-14.json"
  else
    REALM_FILE="realm-export.json"
  fi

  # Combine the realm and user config and send it to the Keycloak server
  HTTP_CODE=$(curl -X POST --data-binary "@$REALM_FILE" \
      -s -o /dev/null -w "%{http_code}" \
      -H "Content-Type: application/json" \
      -H "Authorization: bearer $KEYCLOAK_TOKEN" \
      "$KEYCLOAK_PATH/admin/realms")
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