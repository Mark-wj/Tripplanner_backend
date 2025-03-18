from rest_framework import serializers
from .models import Trip, LogSheet

class LogSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogSheet
        fields = '__all__'

class TripSerializer(serializers.ModelSerializer):
    logs = LogSheetSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = '__all__'