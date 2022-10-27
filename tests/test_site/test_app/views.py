from rest_framework.response import Response
from rest_framework.views import APIView


class Simple(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class WhoAmI(APIView):
    def get(self, request):
        if request.user.is_anonymous:
            return Response({"is_anonymous": True})
        user_data = {
            "is_anonymous": False,
            "username": request.user.username,
            "email": request.user.email,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
        }
        return Response(user_data)
