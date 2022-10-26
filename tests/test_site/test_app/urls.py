from django.urls import path
from test_app.views import Simple

app_name = "test_app"

urlpatterns = [
    path("simple/", Simple.as_view(), name="simple"),
]
