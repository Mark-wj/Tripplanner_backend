from rest_framework import serializers
from .models import Driver

class DriverRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Driver
        fields = (
            'username',
            'password',
            'carrier',                 # Name of Carrier or Carriers
            'truck_number',            # Truck/Tractor & Trailer #
            'home_terminal_address',   # Home Terminal Address
            'shipping_docs',           # Shipping Documents info
            'driver_signature',        # Driver Signature (e.g., base64 string)
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        driver = Driver(**validated_data)
        driver.set_password(password)
        driver.save()
        return driver
