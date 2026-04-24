from rest_framework import serializers

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):

    worker_user_id = serializers.IntegerField(source="worker.id", read_only=True)
    worker_name = serializers.CharField(source="worker.username", read_only=True)
    phone = serializers.CharField(source="worker.phone", read_only=True)

    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ["worker", "status"]

    def validate(self, data):
        slot = data["slot"]
        if slot.available_slots <= 0:
            raise serializers.ValidationError("No slots available")
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        return Booking.objects.create(worker=user, **validated_data)
