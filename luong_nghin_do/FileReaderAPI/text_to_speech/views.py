import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from gtts import gTTS
import uuid

class TextToSpeechAPIView(APIView):
    def post(self, request):
        # Lấy dữ liệu từ request
        text = request.data.get('text', '')
        lang = request.data.get('lang', 'en')  # Ngôn ngữ mặc định là tiếng Anh

        if not text:
            return Response({'error': 'Text is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Tạo tên file duy nhất cho file âm thanh
            file_name = f"{uuid.uuid4()}.mp3"
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)

            # Tạo file âm thanh từ văn bản
            tts = gTTS(text=text, lang=lang)
            tts.save(file_path)

            # Trả về URL để truy cập file âm thanh
            file_url = f"{settings.MEDIA_URL}{file_name}"
            return Response({'audio_url': file_url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)