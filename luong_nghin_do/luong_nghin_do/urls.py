
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
urlpatterns = [
    path('', include('api.urls')),
    path('api/', include('file_reader.urls')),
    path('api/', include('speech_to_text.urls')),
    path('api/', include('text_to_speech.urls')),
    path('api/', include('speech_to_text.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)