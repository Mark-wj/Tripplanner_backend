from django.urls import path
from .views import (
    TripListCreateAPIView,
    TripDetailAPIView,
    RouteMapAPIView,
    GenerateLogSheetAPIView
)

urlpatterns = [
    path('trips/', TripListCreateAPIView.as_view(), name='trip-list-create'),
    path('trips/<int:pk>/', TripDetailAPIView.as_view(), name='trip-detail'),
    path('trips/<int:trip_id>/route_map/', RouteMapAPIView.as_view(), name='route-map'),
    path('trips/<int:trip_id>/generate_logs/', GenerateLogSheetAPIView.as_view(), name='generate-logsheet'),
]
