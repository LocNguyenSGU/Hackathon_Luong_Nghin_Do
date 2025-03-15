from rest_framework import viewsets
from .models import UserDetail
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = UserDetail.objects.all()
    serializer_class = UserSerializer