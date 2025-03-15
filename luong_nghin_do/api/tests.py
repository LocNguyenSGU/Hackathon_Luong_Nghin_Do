from rest_framework import serializers
from .models import UserDetail, ChuDe, File, DanhGia

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDetail
        fields = '__all__'

class ChuDeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChuDe
        fields = '__all__'

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

class DanhGiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DanhGia
        fields = '__all__'
