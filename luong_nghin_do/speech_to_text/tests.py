import io
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from pydub import AudioSegment
from .views import AudioToTextView
class AudioToTextViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('audio-to-text')  # ⚠️ Tên name của URL cần là 'audio_to_text'

    @patch('speech_to_text.views.AudioToTextView.convert_audio_to_text') 
    def test_upload_valid_wav_file(self, mock_convert):
        # Mock kết quả chuyển đổi
        mock_convert.return_value = "Đây là nội dung từ file audio"

        # Tạo file WAV giả
        file_content = io.BytesIO(b"RIFF....WAVEfmt ")  # Dữ liệu giả WAV
        file_content.name = 'test.wav'

        response = self.client.post(self.url, {'file': file_content}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], "Đây là nội dung từ file audio")

    @patch('speech_to_text.views.AudioToTextView.convert_audio_to_text')
    def test_upload_invalid_format(self, mock_convert):
        # Tạo file không hỗ trợ
        file_content = io.BytesIO(b"Fake data")
        file_content.name = 'test.txt'

        response = self.client.post(self.url, {'file': file_content}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Unsupported audio format")

    def test_no_file_uploaded(self):
        response = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)  # Expect serializer error for missing 'file'