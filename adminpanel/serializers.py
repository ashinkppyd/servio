from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "district",
            "state",
            "is_active",
            "role",
        ]


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "company_name",
            "district",
            "state",
            "is_active",
            "role",
        ]
