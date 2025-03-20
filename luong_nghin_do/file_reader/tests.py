import io
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile


class FileUploadAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/upload/"  # Đảm bảo trùng URL

    def test_upload_no_file(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'No file uploaded')

    def test_upload_unsupported_file_type(self):
        file = SimpleUploadedFile("test.txt", b"Hello", content_type="text/plain")
        response = self.client.post(self.url, {'file': file}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Unsupported file type')

    @patch('file_reader.views.fitz.open')  # Mock PyMuPDF
    def test_upload_pdf_file(self, mock_fitz_open):
        # Giả lập trang PDF có text
        mock_pdf = mock_fitz_open.return_value.__enter__.return_value
        mock_pdf.__iter__.return_value = [mock_page := mock_pdf.page()]
        mock_page.get_text.return_value = "Mock PDF Text"

        file = SimpleUploadedFile("test.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.client.post(self.url, {'file': file}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertIn("Mock PDF Text", response.data['content'])

    @patch('file_reader.views.docx.Document')
    def test_upload_docx_file(self, mock_docx):
        mock_doc = mock_docx.return_value
        mock_doc.paragraphs = [type('MockPara', (), {'text': 'Paragraph 1'})(),
                               type('MockPara', (), {'text': 'Paragraph 2'})()]
        file = SimpleUploadedFile("test.docx", b"fake-docx-content", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response = self.client.post(self.url, {'file': file}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertIn("Paragraph 1", response.data['content'])

    @patch('file_reader.views.pptx.Presentation')
    def test_upload_pptx_file(self, mock_pptx):
        mock_presentation = mock_pptx.return_value
        mock_slide = type('MockSlide', (), {
            'shapes': [type('MockShape', (), {'text': 'Slide Text'})()]
        })()
        mock_presentation.slides = [mock_slide]
        file = SimpleUploadedFile("test.pptx", b"fake-pptx-content", content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        response = self.client.post(self.url, {'file': file}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertIn("Slide Text", response.data['content'])


class UploadImageViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/uploadFile/"  # Đảm bảo đúng URL

    def test_upload_no_file(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'No file provided')

    @patch('file_reader.views.cloudinary.uploader.upload')
    def test_upload_image_success(self, mock_upload):
        mock_upload.return_value = {'secure_url': 'https://mocked.cloudinary.url/image.jpg'}
        file = SimpleUploadedFile("image.jpg", b"fake-image-content", content_type="image/jpeg")
        response = self.client.post(self.url, {'file': file}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['url'], 'https://mocked.cloudinary.url/image.jpg')