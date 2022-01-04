from rest_framework.routers import DefaultRouter

from django_keycloak.api.views import UserProfileAPIView

django_keycloak_router = DefaultRouter()
django_keycloak_router.register(r'users', UserProfileAPIView)
