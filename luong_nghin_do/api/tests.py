import json
import unittest
from unittest.mock import patch, MagicMock
from django.http import JsonResponse, HttpRequest
from .views import summarize_text_hierarchical, generate_exercises, summarize_text_short, chat_with_ai
from django.test import TestCase, Client, RequestFactory
from .models import ChuDe, DanhGia
from django.contrib.auth import get_user_model
User = get_user_model()

class SummarizeTextHierarchicalTest(unittest.TestCase):

    def setUp(self):
        self.valid_text = "Đây là văn bản mẫu để kiểm tra chức năng tóm tắt."
        self.mock_summary_json = {
            "title": "Chủ đề chính",
            "children": [
                {"title": "Ý chính 1"},
                {"title": "Ý chính 2"}
            ]
        }

    def _create_mock_request(self, text, mode="normal", method="POST"):
        request = HttpRequest()
        request.method = method
        body_dict = {"text": text, "mode": mode}
        request._body = json.dumps(body_dict).encode('utf-8')
        return request

    @patch("api.views.client.chat.completions.create")
    def test_valid_request_returns_summary(self, mock_openai):
        # Mock OpenAI API trả về JSON hợp lệ
        mock_response = MagicMock()
        mock_response.choices[0].message.content = f"""```json\n{json.dumps(self.mock_summary_json)}\n```"""
        mock_openai.return_value = mock_response

        request = self._create_mock_request(self.valid_text, mode="basic")
        response = summarize_text_hierarchical(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["summary"], self.mock_summary_json)
        self.assertEqual(data["mode"], "basic")

    def test_missing_text_returns_error(self):
        request = self._create_mock_request(text="", mode="normal")
        response = summarize_text_hierarchical(request)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Vui lòng nhập văn bản!")


    def test_invalid_method_returns_error(self):
        request = self._create_mock_request(text=self.valid_text, method="GET")
        response = summarize_text_hierarchical(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid request method", response.content.decode())

    @patch("api.views.client.chat.completions.create")
    def test_invalid_json_from_openai(self, mock_openai):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```json\nKhông phải JSON hợp lệ\n```"
        mock_openai.return_value = mock_response

        request = self._create_mock_request(self.valid_text, mode="normal")
        response = summarize_text_hierarchical(request)
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "OpenAI trả về dữ liệu không đúng JSON")

    def test_invalid_json_request_body(self):
        request = HttpRequest()
        request.method = "POST"
        request._body = b"khong phai json"
        response = summarize_text_hierarchical(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid JSON format", response.content.decode())
        

class GenerateExercisesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/generate-exercise/'  # Đảm bảo URL đúng với routes của bạn
        self.valid_text = "Trí tuệ nhân tạo là lĩnh vực nghiên cứu và phát triển máy móc thông minh."
        self.valid_types = ["multiple_choice", "fill_in_the_blank", "short_answer"]
        self.mock_response_jsons = {
            "multiple_choice": {
                "type": "multiple_choice",
                "question": "AI là viết tắt của từ nào?",
                "options": ["Artificial Intelligence", "Advanced Internet", "Automatic Input", "Audio Interface"],
                "correct_answer": "Artificial Intelligence"
            },
            "fill_in_the_blank": {
                "type": "fill_in_the_blank",
                "question": "_____ là một lĩnh vực nghiên cứu trong AI.",
                "correct_answer": "Học máy"
            },
            "short_answer": {
                "type": "short_answer",
                "question": "Học máy là gì?",
                "correct_answer": "Học máy là một lĩnh vực của AI nghiên cứu cách máy tính có thể học từ dữ liệu."
            }
        }

    @patch("api.views.client.chat.completions.create")
    def test_generate_exercises_success(self, mock_openai):
        for exercise_type in self.valid_types:
            mock_exercise = self.mock_response_jsons[exercise_type]
            mock_content = f"```json\n{json.dumps(mock_exercise, ensure_ascii=False)}\n```"

            mock_response = MagicMock()
            mock_response.choices[0].message.content = mock_content
            mock_openai.return_value = mock_response

            response = self.client.post(
                self.url,
                data=json.dumps({"text": self.valid_text, "type": exercise_type}),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["exercise"], mock_exercise)

    def test_invalid_method(self):
        response = self.client.get(self.url)  # GET request
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid request method", response.content.decode())

    def test_missing_text(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"text": "", "type": "multiple_choice"}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Vui lòng nhập nội dung để tạo bài tập")

    def test_invalid_type(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"text": "Some text", "type": "invalid_type"}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Loại bài tập không hợp lệ")

    @patch('api.views.client.chat.completions.create')
    def test_invalid_json_from_openai(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```json { invalid_json ```"
        mock_create.return_value = mock_response

        response = self.client.post(
            self.url,
            data=json.dumps({"text": "Some text", "type": "multiple_choice"}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Phản hồi từ OpenAI không đúng JSON")

    @patch('api.views.client.chat.completions.create')
    def test_exception_handling(self, mock_create):
        mock_create.side_effect = Exception("Lỗi không mong muốn từ API")

        response = self.client.post(
            self.url,
            data=json.dumps({"text": "Some text", "type": "multiple_choice"}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Lỗi không mong muốn từ API")


class SummarizeTextShortTests(TestCase):
    def setUp(self):
        self.valid_text = (
            "Trí tuệ nhân tạo là lĩnh vực nghiên cứu nhằm phát triển máy móc có khả năng tư duy, "
            "học hỏi và đưa ra quyết định giống như con người. Công nghệ này đang được ứng dụng trong nhiều lĩnh vực như y tế, giáo dục, giao thông và tài chính."
        )
        self.mock_response_data = {
            "title": "Trí tuệ nhân tạo",
            "summary": "Trí tuệ nhân tạo phát triển máy móc có khả năng tư duy, học hỏi, ứng dụng trong y tế, giáo dục, giao thông, tài chính."
        }

    def _create_mock_request(self, text, method="POST"):
        request = HttpRequest()
        request.method = method
        request._body = json.dumps({"text": text}).encode('utf-8')
        return request

    @patch("api.views.client.chat.completions.create")
    def test_summarize_text_success(self, mock_openai):
        """
        ✅ Test thành công khi tóm tắt văn bản hợp lệ.
        """
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(self.mock_response_data, ensure_ascii=False)
        mock_openai.return_value = mock_response

        request = self._create_mock_request(self.valid_text)
        response = summarize_text_short(request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)

        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["title"], self.mock_response_data["title"])
        self.assertEqual(response_data["summary"], self.mock_response_data["summary"])

    def test_invalid_method(self):
        """
        ❌ Test method không phải POST.
        """
        request = self._create_mock_request(self.valid_text, method="GET")
        response = summarize_text_short(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid request method", response.content.decode())

    def test_missing_text(self):
        """
        ❌ Test thiếu hoặc rỗng trường text.
        """
        request = self._create_mock_request("", method="POST")
        response = summarize_text_short(request)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["error"], "Vui lòng nhập văn bản!")

    @patch("api.views.client.chat.completions.create")
    def test_invalid_json_from_openai(self, mock_openai):
        """
        ❌ Test phản hồi từ OpenAI không phải JSON hợp lệ.
        """
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```json { invalid json ```"
        mock_openai.return_value = mock_response

        request = self._create_mock_request(self.valid_text)
        response = summarize_text_short(request)
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["error"], "Phản hồi từ AI không phải JSON hợp lệ")

    @patch("api.views.client.chat.completions.create")
    def test_unexpected_exception(self, mock_openai):
        """
        ❌ Test lỗi không mong muốn từ OpenAI.
        """
        mock_openai.side_effect = Exception("Lỗi hệ thống OpenAI")

        request = self._create_mock_request(self.valid_text)
        response = summarize_text_short(request)
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertIn("Lỗi hệ thống OpenAI", response_data["error"])

    def test_invalid_json_request_body(self):
        """
        ❌ Test lỗi JSON không hợp lệ từ request.
        """
        request = HttpRequest()
        request.method = "POST"
        request._body = b"{invalid json}"
        response = summarize_text_short(request)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["error"], "Invalid JSON format")
        
class ChatWithAiTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Tạo chủ đề mẫu
        self.chu_de = ChuDe.objects.create(name_chu_de="Toán học", noi_dung="Giải phương trình bậc hai")

    @patch("api.views.DanhGia.objects.get_or_create")
    @patch("api.views.client")  # patch cũ
    def test_chat_with_valid_input_creates_thread_and_returns_response(self, mock_client, mock_get_or_create):
        # Mock get_or_create
        mock_danh_gia = MagicMock(idThread=None, soCauHoi=0)
        mock_get_or_create.return_value = (mock_danh_gia, True)

        # Mock client như cũ
        mock_thread = MagicMock(id="thread_test_id")
        mock_client.beta.threads.create.return_value = mock_thread
        mock_client.beta.threads.messages.create.return_value = None
        mock_run = MagicMock(id="run_test_id", status="completed")
        mock_client.beta.threads.runs.create.return_value = mock_run
        mock_client.beta.threads.runs.retrieve.return_value = mock_run

        mock_message = MagicMock()
        mock_message.role = "assistant"
        mock_message.content = [MagicMock(text=MagicMock(value="Đây là câu trả lời từ AI."))]
        mock_client.beta.threads.messages.list.return_value.data = [mock_message]

        payload = {
            "idUser": 1,
            "idChuDe": self.chu_de.id,
            "message": "Giải phương trình x^2 + 5x + 6 = 0"
        }

        request = self.factory.post("/chat", data=json.dumps(payload), content_type="application/json")

        response = chat_with_ai(request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["thread_id"], "thread_test_id")
        self.assertEqual(response_data["response"], "Đây là câu trả lời từ AI.")

    def test_chat_with_missing_fields_returns_error(self):
        payload = {
            "idUser": 1,
            "message": "Thiếu idChuDe"
        }
        request = self.factory.post("/chat", data=json.dumps(payload), content_type="application/json")
        response = chat_with_ai(request)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn("Vui lòng nhập", response_data["error"])
        
    def test_chat_with_non_post_method(self):
        request = self.factory.get("/chat")
        response = chat_with_ai(request)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["error"], "Invalid request method")

    def test_chat_with_invalid_json(self):
        request = self.factory.post("/chat", data="không phải json", content_type="application/json")
        response = chat_with_ai(request)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn("Dữ liệu JSON không hợp lệ", response_data["error"])

from rest_framework import status
from rest_framework.test import APITestCase
from api.models import UserDetail
class CheckUserTestCase(APITestCase):
    def setUp(self):
        self.user = UserDetail.objects.create(
            lastName="testuser",
            firstName="a",
            email="test@example.com",
            password="testpass"  # Bạn có thể mã hóa nếu muốn
        )

    def test_check_user_success(self):
        data = {"username": "testuser", "password": "testpass"}
        response = self.client.post("/check-user/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.idUser)

    def test_check_user_missing_fields(self):
        data = {"username": "testuser"}  # thiếu password
        response = self.client.post("/check-user/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Vui lòng nhập đầy đủ username và password")

    def test_check_user_invalid_credentials(self):
        data = {"username": "testuser", "password": "wrongpass"}
        response = self.client.post("/check-user/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Tài khoản không tồn tại")
        
class RegisterUserTestCase(APITestCase):
    def setUp(self):
        self.existing_user = UserDetail.objects.create(
            lastName="existinguser",
            firstName="a",
            email="exist@example.com",
            password="password123"
        )

    def test_register_user_success(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass"
        }
        response = self.client.post("/register/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Đăng ký thành công")
        self.assertTrue(UserDetail.objects.filter(email="new@example.com").exists())

    def test_register_user_missing_fields(self):
        data = {"username": "newuser", "email": "new@example.com"}  # thiếu password
        response = self.client.post("/register/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Vui lòng nhập đầy đủ username, email và password")

    def test_register_user_email_exists(self):
        data = {
            "username": "anotheruser",
            "email": "exist@example.com",  # email đã tồn tại
            "password": "pass123"
        }
        response = self.client.post("/register/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Email đã được sử dụng")
from .views import split_text
class TestSplitText(unittest.TestCase):
    def test_short_text(self):
        text = "Đây là một câu ngắn."
        result = split_text(text)
        self.assertEqual(result, [text.strip()])

    def test_exact_max_length(self):
        sentence = "a" * 998  # 998 ký tự
        text = sentence + ". "
        result = split_text(text, max_length=1000)
        self.assertEqual(result, [text.strip()])

    def test_long_text_split(self):
        text = "Câu thứ nhất. Câu thứ hai. Câu thứ ba."
        result = split_text(text, max_length=20)
        self.assertTrue(len(result) > 1)
        for chunk in result:
            self.assertLessEqual(len(chunk), 20)

    def test_empty_text(self):
        text = ""
        result = split_text(text)
        self.assertEqual(result, [])

    def test_chunk_not_exceed_max_length(self):
        text = "Một. Hai. Ba. Bốn. Năm. Sáu. Bảy. Tám. Chín. Mười."
        result = split_text(text, max_length=20)
        for chunk in result:
            self.assertLessEqual(len(chunk), 20)

from unittest.mock import patch, MagicMock
import json

from .views import summarize_chunk 

class TestSummarizeChunk(unittest.TestCase):

    @patch("api.views.client.chat.completions.create")  # 👉 mock OpenAI
    def test_successful_response(self, mock_create):
        # Giả lập response hợp lệ
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "title": "Tiêu đề mẫu",
            "summary": "Đây là bản tóm tắt mẫu của văn bản."
        })
        mock_create.return_value = mock_response

        title, summary = summarize_chunk("Đây là văn bản mẫu cần tóm tắt.")

        self.assertEqual(title, "Tiêu đề mẫu")
        self.assertEqual(summary, "Đây là bản tóm tắt mẫu của văn bản.")

    @patch("api.views.client.chat.completions.create")
    def test_invalid_json_response(self, mock_create):
        # Giả lập response không phải JSON
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Không phải JSON"
        mock_create.return_value = mock_response

        title, summary = summarize_chunk("Văn bản bất kỳ")

        self.assertEqual(title, "")
        self.assertEqual(summary, "Phản hồi từ AI không hợp lệ")

    @patch("api.views.client.chat.completions.create")
    def test_api_exception(self, mock_create):
        # Giả lập lỗi từ API
        mock_create.side_effect = Exception("Mạng lỗi")

        title, summary = summarize_chunk("Văn bản bất kỳ")

        self.assertEqual(title, "")
        self.assertEqual(summary, "Lỗi khi tóm tắt văn bản")