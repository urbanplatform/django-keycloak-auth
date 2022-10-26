from rest_framework.response import Response
from rest_framework.views import APIView


class Simple(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class WhoAmI(APIView):
    def get(self, request):
        user_data = {
            "username": request.context.user.username,
            "email": request.context.user.email,
            "first_name": request.context.user.first_name,
            "last_name": request.context.user.last_name,
        }
        return Response(user_data)
