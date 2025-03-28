from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class Driver(AbstractUser):
    # Override the groups field with a unique related_name.
    groups = models.ManyToManyField(
        Group,
        related_name="driver_set",  # or any unique name like "custom_driver_set"
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups"
    )
    # Override the user_permissions field with a unique related_name.
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="driver_set",  # or "custom_driver_permissions"
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions"
    )
    
    # Additional driver profile fields:
    carrier = models.CharField(max_length=255)
    truck_number = models.CharField(max_length=100)
    home_terminal_address = models.CharField(max_length=255)
    shipping_docs = models.CharField(max_length=255)
    driver_signature = models.TextField()

    def __str__(self):
        return self.username
