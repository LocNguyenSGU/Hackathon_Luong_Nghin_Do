from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .views import summarize_text_hierarchical


router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('summarize/', summarize_text_hierarchical, name='summarize-text'),
]