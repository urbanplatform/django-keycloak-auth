#!/bin/bash

# Exit with nonzero exit code if anything fails
set -eo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

echo "Waiting for Keycloak to launch on $KEYCLOAK_HOST:$KEYCLOAK_PORT..."
# Abort after 10 seconds to avoid blocking (-m --> max time)
while ! curl -s -f -o /dev/null -m 2 "http://$KEYCLOAK_HOST:$KEYCLOAK_PORT/auth/realms/master"; do
  echo "Waiting..."
  sleep 2 &
  wait
done

poetry run test_site/manage.py test test_app