from django.urls import path
from .views import DriverRegistrationView, DriverLoginView, LogoutView

urlpatterns = [
    path('register/', DriverRegistrationView.as_view(), name='register'),
    path('login/', DriverLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
