from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .views import summarize_text_hierarchical, generate_exercises, summarize_text
from .views import UserDetailViewSet, ChuDeViewSet, FileViewSet, DanhGiaViewSet


router = DefaultRouter()
router.register(r'users', UserDetailViewSet)
router.register(r'chude', ChuDeViewSet)
router.register(r'files', FileViewSet)
router.register(r'danhgia', DanhGiaViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('summarize/', summarize_text_hierarchical, name='summarize-text'),
    path('generate-exercise/', generate_exercises, name='generate-exercise'),
    path('summarize-text/', summarize_text, name='summarize-text'),
]