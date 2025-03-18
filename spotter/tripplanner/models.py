from django.db import models

# Create your models here.
class Trip(models.Model):
    driver_name = models.CharField(max_length=150)
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_hours = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip by {self.driver_name} on {self.created_at.strftime('%Y-%m-%d')}"
    
class LogSheet(models.Model):
    trip = models.ForeignKey(Trip, related_name='logs', on_delete=models.CASCADE)
    log_date = models.DateField()
    driving_hours = models.FloatField
    rest_periods = models.FloatField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Log for {self.trip} on {self.log_date}"