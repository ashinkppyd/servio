from rest_framework import serializers
from .models import User
import re


class WorkerRegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone',
            'state',
            'district',
            'place',
            'password',
            'confirm_password'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):

        for field in self.Meta.fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} is required")

        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        password = data['password']

        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", password):
            raise serializers.ValidationError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", password):
            raise serializers.ValidationError("Password must contain lowercase letter")
        if not re.search(r"[0-9]", password):
            raise serializers.ValidationError("Password must contain a number")
        if not re.search(r"[!@#$%^&*]", password):
            raise serializers.ValidationError("Password must contain special character")

        email = data.get("email")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise serializers.ValidationError("Invalid email format")

        phone = data.get("phone")
        if not re.match(r"^[6-9]\d{9}$", phone):
            raise serializers.ValidationError("Invalid phone number")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            state=validated_data.get('state'),
            district=validated_data.get('district'),
            place=validated_data.get('place'),
            password=validated_data['password'],
            role='worker'
        )
        return user



class CompanyRegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = [
            'company_name',
            'email',
            'phone',
            'state',
            'district',
            'place',
            'password',
            'confirm_password'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    def validate(self, data):

        for field in self.Meta.fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} is required")

        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        password = data['password']

        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", password):
            raise serializers.ValidationError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", password):
            raise serializers.ValidationError("Password must contain lowercase letter")
        if not re.search(r"[0-9]", password):
            raise serializers.ValidationError("Password must contain a number")
        if not re.search(r"[!@#$%^&*]", password):
            raise serializers.ValidationError("Password must contain special character")

        email = data.get("email")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise serializers.ValidationError("Invalid email format")

        phone = data.get("phone")
        if not re.match(r"^[6-9]\d{9}$", phone):
            raise serializers.ValidationError("Invalid phone number")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data.get('company_name'),
            email=validated_data['email'],
            phone=validated_data['phone'],
            company_name=validated_data.get('company_name'),
            state=validated_data.get('state'),
            district=validated_data.get('district'),
            place=validated_data.get('place'),
            password=validated_data['password'],
            role='company'
        )
        return user
    

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"