from django.urls import path
from .views import AudioToTextView

urlpatterns = [
    path('audio-to-text/', AudioToTextView.as_view(), name='audio-to-text'),
]
