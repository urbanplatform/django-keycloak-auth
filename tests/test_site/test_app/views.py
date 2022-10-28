from rest_framework.response import Response
from rest_framework.views import APIView


class Simple(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class WhoAmI(APIView):
    def get(self, request):
        if request.user.is_anonymous:
            return Response({"isAnonymous": True})
        user_data = {
            "isAnonymous": False,
            "username": request.user.username,
            "email": request.user.email,
            "firstName": request.user.first_name,
            "lastName": request.user.last_name,
        }
        return Response(user_data)
