import os
import speech_recognition as sr
from pydub import AudioSegment
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .serializers import AudioUploadSerializer

class AudioToTextView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = AudioUploadSerializer(data=request.data)
        if serializer.is_valid():
            audio_file = serializer.validated_data['file']
            file_extension = os.path.splitext(audio_file.name)[1].lower()

            if file_extension not in ['.wav', '.mp3', '.ogg']:
                return Response({"error": "Unsupported audio format"}, status=status.HTTP_400_BAD_REQUEST)

            text = self.convert_audio_to_text(audio_file, file_extension)
            return Response({"text": text}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def convert_audio_to_text(self, file, file_extension):
        recognizer = sr.Recognizer()

        # Chuyển đổi file MP3, OGG sang WAV
        if file_extension != '.wav':
            audio = AudioSegment.from_file(file, format=file_extension[1:])
            file = "temp_audio.wav"
            audio.export(file, format="wav")

        with sr.AudioFile(file) as source:
            audio_data = recognizer.record(source)

        try:
            return recognizer.recognize_google(audio_data, language="vi-VN")  # Hỗ trợ tiếng Việt
        except sr.UnknownValueError:
            return "Không thể nhận diện giọng nói"
        except sr.RequestError:
            return "Lỗi kết nối đến dịch vụ nhận diện giọng nói"
