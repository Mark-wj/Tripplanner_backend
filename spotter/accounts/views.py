from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import DriverRegistrationSerializer
from .models import Driver

# Registration View using APIView
class DriverRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DriverRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Login View using APIView
class DriverLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"msg": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate the driver using Django's authentication system
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"msg": "Bad username or password"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate tokens using Simple JWT's RefreshToken
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)

# Logout View (blacklists the refresh token) using APIView
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # Ensure you have configured token blacklisting in settings.py
            return Response({"msg": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Bad token"}, status=status.HTTP_400_BAD_REQUEST)
