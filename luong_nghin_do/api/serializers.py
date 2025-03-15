from rest_framework import serializers
from .models import UserDetail

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDetail
        fields = '__all__'