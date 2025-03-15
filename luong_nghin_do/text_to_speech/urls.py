from django.urls import path
from .views import TextToSpeechAPIView

urlpatterns = [
    path('tts/', TextToSpeechAPIView.as_view(), name='text-to-speech'),
]