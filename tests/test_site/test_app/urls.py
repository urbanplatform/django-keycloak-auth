from django.urls import path
from test_app.views import Simple, WhoAmI

app_name = "test_app"

urlpatterns = [
    path("simple/", Simple.as_view(), name="simple"),
    path("who-am-i/", WhoAmI.as_view(), name="who_am_i"),
]
