import base64
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Trip
from .serializers import TripSerializer
from .utils import get_route, generate_daily_logs

class TripListCreateAPIView(APIView):
    """
    API view for listing trips for the logged-in driver or, if permitted, for another user,
    and creating a new trip.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        # Check if a user_id query parameter is provided
        user_id = request.query_params.get("user_id")
        
        if user_id:
            # Convert user_id to integer and check permissions:
            # Allow if user is staff or if the user_id matches the logged-in user's id.
            try:
                user_id = int(user_id)
            except ValueError:
                return Response({"detail": "Invalid user_id parameter."},
                                status=status.HTTP_400_BAD_REQUEST)

            if request.user.is_staff or user_id == request.user.id:
                trips = Trip.objects.filter(driver_id=user_id)
            else:
                return Response(
                    {"detail": "Permission denied to view trips for this user."},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # No query parameter: return trips for the authenticated user.
            trips = Trip.objects.filter(driver=request.user)
        
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = TripSerializer(data=request.data)
        if serializer.is_valid():
            # Automatically assign the logged-in driver to the trip.
            serializer.save(driver=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TripDetailAPIView(APIView):
    """
    API view for retrieving, updating, or deleting a trip owned by the logged-in driver.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(Trip, pk=pk, driver=user)

    def get(self, request, pk, format=None):
        trip = self.get_object(pk, request.user)
        serializer = TripSerializer(trip)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        trip = self.get_object(pk, request.user)
        serializer = TripSerializer(trip, data=request.data)
        if serializer.is_valid():
            serializer.save(driver=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        trip = self.get_object(pk, request.user)
        serializer = TripSerializer(trip, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(driver=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        trip = self.get_object(pk, request.user)
        trip.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RouteMapAPIView(APIView):
    """
    API view to return route details from OSRM for a trip owned by the logged-in driver.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id, format=None):
        trip = get_object_or_404(Trip, pk=trip_id, driver=request.user)
        try:
            route_data = get_route(trip.current_location, trip.pickup_location, trip.dropoff_location)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(route_data, status=status.HTTP_200_OK)

class GenerateLogSheetAPIView(APIView):
    """
    API view to dynamically generate daily log sheets (JSON) for a trip.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id, format=None):
        trip = get_object_or_404(Trip, pk=trip_id, driver=request.user)
        try:
            route_data = get_route(trip.current_location, trip.pickup_location, trip.dropoff_location)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logs = generate_daily_logs(trip, route_data)
        return Response(logs, status=status.HTTP_200_OK)
