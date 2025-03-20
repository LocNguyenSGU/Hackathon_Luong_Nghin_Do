from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from django.conf import settings
import os

class TextToSpeechAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/tts/'  # Cập nhật URL này nếu khác
        self.text = 'Hello world'
        self.lang = 'en'

    @patch('text_to_speech.views.gTTS')  # Giả sử view nằm trong speech_to_text/views.py
    def test_post_valid_text(self, mock_gtts_class):
        # Mock phương thức save để không tạo file thật
        mock_tts_instance = MagicMock()
        mock_gtts_class.return_value = mock_tts_instance

        response = self.client.post(self.url, {'text': self.text, 'lang': self.lang}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('audio_url', response.data)

        # Kiểm tra file URL đúng định dạng
        file_url = response.data['audio_url']
        self.assertTrue(file_url.startswith(settings.MEDIA_URL))
        self.assertTrue(file_url.endswith('.mp3'))

        # Kiểm tra gTTS được gọi đúng
        mock_gtts_class.assert_called_once_with(text=self.text, lang=self.lang)
        mock_tts_instance.save.assert_called_once()
    
    def test_post_missing_text(self):
        response = self.client.post(self.url, {'lang': self.lang}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Text is required')

    @patch('text_to_speech.views.gTTS')
    def test_post_gtts_raises_exception(self, mock_gtts_class):
        mock_gtts_class.side_effect = Exception('Something went wrong')

        response = self.client.post(self.url, {'text': self.text, 'lang': self.lang}, format='json')
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Something went wrong')