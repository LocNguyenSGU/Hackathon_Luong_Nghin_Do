from django.urls import path
from .views import FileUploadAPIView
from .views import UploadImageView
urlpatterns = [
    path("upload/", FileUploadAPIView.as_view(), name="file-upload"),
    path('uploadFile/', UploadImageView.as_view(), name='upload_image'),
]
