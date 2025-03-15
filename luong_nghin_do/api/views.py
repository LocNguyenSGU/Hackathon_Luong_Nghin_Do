from rest_framework import viewsets
from .models import UserDetail
from .serializers import UserDetailSerializer
import openai
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import re

class UserViewSet(viewsets.ModelViewSet):
    queryset = UserDetail.objects.all()
    serializer_class = UserDetailSerializer
    
    # 🔹 Khởi tạo client OpenAI theo chuẩn mới nhất
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

@csrf_exempt
def summarize_text_hierarchical(request):
    """
    API nhận văn bản dài từ request, gửi đến OpenAI và trả về JSON phân cấp.
    Hỗ trợ 3 chế độ tóm tắt: basic, normal, detailed.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        # 🔹 Lấy nội dung từ request
        data = json.loads(request.body)
        input_text = data.get("text", "").strip()
        mode = data.get("mode", "normal").strip().lower()  # Default: normal

        if not input_text:
            return JsonResponse({"error": "Vui lòng nhập văn bản!"}, status=400)

        # 📌 Chọn prompt tùy theo chế độ
        if mode == "basic":
            prompt = f"""
            Hãy tóm tắt nội dung sau theo cách ngắn gọn nhất, chỉ giữ lại những ý chính lớn.
            
            Nội dung:
            {input_text}
            
            Xuất ra JSON hợp lệ với định dạng sau:
            ```json
            {{
              "title": "Chủ đề chính",
              "children": [
                {{"title": "Ý chính 1"}},
                {{"title": "Ý chính 2"}}
              ]
            }}
            ```
            """
        elif mode == "detailed":
            prompt = f"""
            Hãy tóm tắt nội dung sau một cách chi tiết, có phân cấp đầy đủ, giải thích từng ý và đưa ví dụ nếu cần.
            
            Nội dung:
            {input_text}
            
            Xuất ra JSON hợp lệ với định dạng sau:
            ```json
            {{
              "title": "Chủ đề chính",
              "children": [
                {{
                  "title": "Ý chính 1",
                  "children": [
                    {{"title": "Giải thích chi tiết 1"}},
                    {{"title": "Ví dụ 1"}}
                  ]
                }},
                {{
                  "title": "Ý chính 2",
                  "children": [
                    {{"title": "Giải thích chi tiết 2"}},
                    {{"title": "Ví dụ 2"}}
                  ]
                }}
              ]
            }}
            ```
            """
        else:  # Default: normal
            prompt = f"""
            Hãy tóm tắt nội dung sau theo dạng phân cấp, đầy đủ nhưng không quá chi tiết.
            
            Nội dung:
            {input_text}
            
            Xuất ra JSON hợp lệ với định dạng sau:
            ```json
            {{
              "title": "Chủ đề chính",
              "children": [
                {{
                  "title": "Ý chính 1",
                  "children": [
                    {{"title": "Ý phụ 1.1"}},
                    {{"title": "Ý phụ 1.2"}}
                  ]
                }},
                {{
                  "title": "Ý chính 2",
                  "children": [
                    {{"title": "Ý phụ 2.1"}},
                    {{"title": "Ý phụ 2.2"}}
                  ]
                }}
              ]
            }}
            ```
            """

        # 📌 Gửi yêu cầu đến OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500  # Giới hạn số token để đảm bảo phản hồi đầy đủ
        )

        # 📌 Lấy nội dung phản hồi từ API
        summary_json = response.choices[0].message.content.strip()

        # 🔍 Loại bỏ dấu ```json ... ```
        summary_json_cleaned = re.sub(r"```json|```", "", summary_json).strip()

        # 📌 Chuyển kết quả từ chuỗi JSON về dạng Python dictionary
        try:
            summary_dict = json.loads(summary_json_cleaned)
        except json.JSONDecodeError:
            return JsonResponse({"error": "OpenAI trả về dữ liệu không đúng JSON", "raw_response": summary_json_cleaned}, status=500)

        return JsonResponse({"status": "success", "summary": summary_dict, "mode": mode}, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def generate_exercises(request):
    """
    API nhận văn bản và loại bài tập (multiple_choice, fill_in_the_blank, short_answer)
    và tạo bài tập tương ứng.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        # 🔹 Nhận dữ liệu từ body JSON
        data = json.loads(request.body)
        text = data.get("text", "").strip()
        exercise_type = data.get("type", "").strip().lower()  # Loại bài tập

        if not text:
            return JsonResponse({"error": "Vui lòng nhập nội dung để tạo bài tập"}, status=400)

        if exercise_type not in ["multiple_choice", "fill_in_the_blank", "short_answer"]:
            return JsonResponse({"error": "Loại bài tập không hợp lệ"}, status=400)

        # 📌 Tạo prompt tương ứng với từng loại bài tập
        if exercise_type == "multiple_choice":
            prompt = f"""
            Tạo nhiều bài tập trắc nghiệm (multiple choice) dựa trên nội dung sau:
            
            {text}
            
            Xuất ra JSON dạng sau:
            ```json
            {{
              "type": "multiple_choice",
              "question": "Câu hỏi?",
              "options": ["A", "B", "C", "D"],
              "correct_answer": "Đáp án đúng"
            }}
            ```
            Chỉ trả về JSON hợp lệ.
            """

        elif exercise_type == "fill_in_the_blank":
            prompt = f"""
            Tạo nhiều bài tập điền vào chỗ trống (fill in the blank) dựa trên nội dung sau:
            
            {text}
            
            Xuất ra JSON dạng sau:
            ```json
            {{
              "type": "fill_in_the_blank",
              "question": "Câu này có một từ bị thiếu: _____ là một công nghệ AI.",
              "correct_answer": "Học máy"
            }}
            ```
            Chỉ trả về JSON hợp lệ.
            """

        elif exercise_type == "short_answer":
            prompt = f"""
            Tạo nhiều câu hỏi tự luận ngắn (short answer) dựa trên nội dung sau:
            
            {text}
            
            Xuất ra JSON dạng sau:
            ```json
            {{
              "type": "short_answer",
              "question": "Học máy là gì?"
            }}
            ```
            Chỉ trả về JSON hợp lệ.
            """

        # 📌 Gửi yêu cầu lên OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # 🔹 Lấy kết quả từ OpenAI và xử lý JSON
        exercises_json = response.choices[0].message.content.strip()
        exercises_json_cleaned = re.sub(r"```json|```", "", exercises_json).strip()
        exercises_dict = json.loads(exercises_json_cleaned)

        return JsonResponse({"status": "success", "exercise": exercises_dict}, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Phản hồi từ OpenAI không đúng JSON"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def summarize_text(request):
    """
    API nhận văn bản dài từ request, gửi đến OpenAI và trả về nội dung đã được tóm tắt.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        # 📌 Lấy nội dung từ request
        data = json.loads(request.body)
        input_text = data.get("text", "").strip()

        if not input_text:
            return JsonResponse({"error": "Vui lòng nhập văn bản!"}, status=400)

        # 📌 Prompt tóm tắt văn bản bình thường
        prompt = f"""
        Hãy tóm tắt nội dung sau một cách súc tích và dễ hiểu:

        {input_text}

        Trả về kết quả dưới dạng văn bản ngắn gọn, dễ hiểu.
        """

        # 📌 Gửi yêu cầu đến OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500  # Giới hạn độ dài tóm tắt
        )

        # 📌 Lấy nội dung phản hồi từ API
        summary_text = response.choices[0].message.content.strip()

        return JsonResponse({"status": "success", "summary": summary_text}, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from rest_framework import viewsets
from .models import UserDetail, ChuDe, File, DanhGia
from .serializers import UserDetailSerializer, ChuDeSerializer, FileSerializer, DanhGiaSerializer

class UserDetailViewSet(viewsets.ModelViewSet):
    queryset = UserDetail.objects.all()
    serializer_class = UserDetailSerializer

class ChuDeViewSet(viewsets.ModelViewSet):
    queryset = ChuDe.objects.all()
    serializer_class = ChuDeSerializer

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

class DanhGiaViewSet(viewsets.ModelViewSet):
    queryset = DanhGia.objects.all()
    serializer_class = DanhGiaSerializer
