from rest_framework import viewsets
from .models import UserDetail
from .serializers import UserDetailSerializer
import openai
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import re
import time
import logging
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

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


import logging

logger = logging.getLogger(__name__)  # 📌 Khởi tạo logger

@csrf_exempt
def summarize_text_short(request):
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

        # 📌 Prompt tóm tắt văn bản + tạo tiêu đề
        prompt = f"""
        Bạn là một chuyên gia tóm tắt. 
        Hãy tóm tắt nội dung sau đầy đủ ý chính, không bỏ qua thông tin quan trọng.

        Văn bản: {input_text}

        Trả về kết quả dưới dạng JSON với đúng cấu trúc sau:
        {{
            "title": "Tiêu đề ngắn (2-4 chữ)",
            "summary": "Phần tóm tắt nội dung chính, dễ hiểu"
        }}
        Chỉ trả về JSON hợp lệ, không có văn bản nào khác.
        """

        # 📌 Gửi yêu cầu đến OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,  # Giới hạn độ dài tóm tắt
            response_format={"type": "json_object"}  # ✅ Định dạng đúng kiểu JSON
        )

        # 📌 Ghi log phản hồi gốc từ OpenAI
        logger.info(f"🔹 Response từ AI: {response}")

        # 📌 Lấy nội dung phản hồi (chuỗi JSON)
        response_data = response.choices[0].message.content
        logger.info(f"🔹 Nội dung phản hồi AI: {response_data}")  # Log chi tiết phản hồi

        # 📌 Chuyển chuỗi JSON thành dictionary
        try:
            parsed_data = json.loads(response_data)
            title = parsed_data.get("title", "").strip()
            summary = parsed_data.get("summary", "").strip()
        except json.JSONDecodeError:
            logger.error("⚠️ Phản hồi từ AI không phải JSON hợp lệ!")  # Ghi log lỗi
            return JsonResponse({"error": "Phản hồi từ AI không phải JSON hợp lệ"}, status=500)

        return JsonResponse({
            "status": "success",
            "title": title,
            "summary": summary
        }, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        logger.error("⚠️ Lỗi JSON từ request!")  # Ghi log lỗi JSON
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        logger.exception(f"⚠️ Lỗi không xác định: {str(e)}")  # Ghi log lỗi chi tiết
        return JsonResponse({"error": str(e)}, status=500)
      
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)      
      
@csrf_exempt
def chat_with_ai(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        user_id = data.get("idUser")
        chu_de_id = data.get("idChuDe")
        user_message = data.get("message", "").strip()

        if not user_id or not chu_de_id or not user_message:
            return JsonResponse({"error": "Vui lòng nhập idUser, idChuDe và tin nhắn!"}, status=400)

        # 📌 Lấy chủ đề
        try:
            chu_de = ChuDe.objects.get(id=chu_de_id)
        except ChuDe.DoesNotExist:
            return JsonResponse({"error": "Chủ đề không tồn tại"}, status=404)

        # 📌 Tạo hoặc lấy thread ID
        danh_gia, created = DanhGia.objects.get_or_create(
            idUser_id=user_id,
            idChuDe_id=chu_de_id,
            defaults={"idThread": None, "soCauHoi": 0}  # ➜ Khởi tạo số câu hỏi là 0
        )

        if danh_gia.idThread is None:
            # 🔹 Tạo thread mới
            thread = client.beta.threads.create()
            danh_gia.idThread = thread.id
            danh_gia.soCauHoi = 0  # Reset số câu hỏi
            danh_gia.save()

            # 🏷 Gửi tin nhắn SYSTEM với nội dung chủ đề
            context_message = f"""
            Bạn là một gia sư thông minh, hỗ trợ sinh viên về chủ đề: {chu_de.name_chu_de}.
            Nội dung chủ đề: {chu_de.noi_dung}

            ✅ Trả lời NGẮN GỌN, tối đa 2-3 câu.
            ✅ Không lan man, chỉ nói về chủ đề này.
            ✅ Nếu câu hỏi nằm ngoài phạm vi chủ đề, hãy từ chối trả lời.
            
            📌 Sau khi sinh viên hỏi 4 câu, hãy đưa ra nhận xét:
            - Điểm mạnh trong câu trả lời của sinh viên.
            - Nội dung còn yếu cần cải thiện.
            - Mức độ tiến bộ so với trước.
            - Động viên và hướng dẫn cách cải thiện.
            """

            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="assistant",
                content=context_message
            )

        thread_id = danh_gia.idThread  # 📌 Lấy thread_id hiện tại

        # 📌 Kiểm tra số câu hỏi để quyết định có nhận xét hay không
        if danh_gia.soCauHoi >= 4:
            # 🎯 Yêu cầu AI đánh giá sinh viên
            feedback_message = """
            Đánh giá tổng quan sau 4 câu hỏi:
            - Điểm mạnh trong câu trả lời của sinh viên.
            - Nội dung còn yếu cần cải thiện.
            - Mức độ tiến bộ so với trước.
            - Động viên và hướng dẫn cách cải thiện.
            """
            
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=feedback_message
            )

            danh_gia.soCauHoi = 0  # 🔄 Reset số câu hỏi sau khi đánh giá
            danh_gia.save()
        else:
            # 📌 Gửi tin nhắn của người dùng
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )

            danh_gia.soCauHoi += 1  # ➕ Tăng số câu hỏi
            danh_gia.save()

        # 📌 Chạy Assistant với giới hạn nội dung
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=settings.OPENAI_ASSISTANT_ID,
            instructions=f"Chỉ trả lời trong phạm vi chủ đề '{chu_de.name_chu_de}'. Không lan man."
        )

        # ⏳ Chờ phản hồi từ AI
        while run.status in ["queued", "in_progress"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == "failed":
            error_message = run.last_error.message if hasattr(run.last_error, "message") else "Không có chi tiết lỗi."
            return JsonResponse({"error": f"AI không thể xử lý yêu cầu! Chi tiết: {error_message}"}, status=500)

        # 📌 Lấy phản hồi AI
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        ai_messages = [msg for msg in messages.data if msg.role == "assistant"]
        if not ai_messages:
            return JsonResponse({"error": "AI không phản hồi!"}, status=500)

        ai_response = ai_messages[0].content[0].text.value  # 🏷 Chỉ lấy câu trả lời gần nhất

        return JsonResponse({
            "status": "success",
            "thread_id": thread_id,
            "response": ai_response
        }, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Dữ liệu JSON không hợp lệ"}, status=400)
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

from rest_framework.decorators import api_view
@api_view(['POST'])
def check_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'message': 'Vui lòng nhập đầy đủ username và password'}, status=400)
    
    user = UserDetail.objects.filter(lastName=username, password=password).first()
    
    if user:
        return Response({'id': user.idUser})
    
    return Response({'message': 'Tài khoản không tồn tại'}, status=404)
@api_view(['POST'])
def register_user(request):
    username = request.data.get('username')  # lastName sẽ đóng vai trò username
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'message': 'Vui lòng nhập đầy đủ username, email và password'}, status=400)
    
    # Kiểm tra xem email đã tồn tại chưa
    if UserDetail.objects.filter(email=email).exists():
        return Response({'message': 'Email đã được sử dụng'}, status=400)

    # Tạo người dùng mới
    user = UserDetail.objects.create(
        lastName=username,  
        firstName='a',  # Luôn là "a"
        email=email,
        password=password # Mã hóa mật khẩu
    )

    return Response({'message': 'Đăng ký thành công', 'id': user.idUser}, status=201)

def split_text(text, max_length=1000):
    """
    Chia văn bản thành các đoạn nhỏ để tránh bị cắt khi tóm tắt.
    """
    sentences = text.split('. ')
    chunks, chunk = [], ""
    for sentence in sentences:
        if len(chunk) + len(sentence) < max_length:
            chunk += sentence + ". "
        else:
            chunks.append(chunk.strip())
            chunk = sentence + ". "
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def summarize_chunk(text_chunk):
    """
    Gửi đoạn văn bản nhỏ đến OpenAI để tóm tắt.
    """
    prompt = f"""
    Bạn là một chuyên gia ngôn ngữ. Hãy tóm tắt văn bản sau một cách súc tích nhưng giữ nguyên các ý chính quan trọng.

    📌 **Yêu cầu:**
    - Tóm tắt đầy đủ ý chính, không bỏ qua thông tin quan trọng.
    - Văn phong dễ hiểu, phù hợp với người đọc phổ thông.
    - Phải giữ nguyên cấu trúc câu quan trọng hoặc mạch ý chính.
    - Trả về kết quả dưới dạng JSON hợp lệ với cấu trúc:
    {{
        "title": "Tiêu đề ngắn (3-6 từ)",
        "summary": "Tóm tắt chính xác nội dung, không dài quá 150 từ"
    }}

    Văn bản: {text_chunk}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,  # Tăng giới hạn để tóm tắt tốt hơn
            response_format={"type": "json_object"}
        )

        # 📌 Ghi log phản hồi
        logger.info(f"🔹 Response từ AI: {response}")

        # 📌 Lấy nội dung phản hồi JSON
        response_data = response.choices[0].message.content
        parsed_data = json.loads(response_data)

        return parsed_data.get("title", "").strip(), parsed_data.get("summary", "").strip()

    except json.JSONDecodeError:
        logger.error("⚠️ Phản hồi từ AI không phải JSON hợp lệ!")
        return "", "Phản hồi từ AI không hợp lệ"
    except Exception as e:
        logger.exception(f"⚠️ Lỗi OpenAI: {str(e)}")
        return "", "Lỗi khi tóm tắt văn bản"
@csrf_exempt
def summarize_text(request):
    """
    API nhận văn bản dài từ request, chia nhỏ nếu cần, gửi đến OpenAI và trả về nội dung đã được tóm tắt.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        # 📌 Nhận văn bản từ request
        data = json.loads(request.body)
        input_text = data.get("text", "").strip()

        if not input_text:
            return JsonResponse({"error": "Vui lòng nhập văn bản!"}, status=400)

        # 📌 Chia nhỏ nếu quá dài
        text_chunks = split_text(input_text, max_length=1000)
        summaries = []

        for chunk in text_chunks:
            title, summary = summarize_chunk(chunk)
            summaries.append(summary)

        # 📌 Gộp các đoạn tóm tắt thành một đoạn hoàn chỉnh
        final_summary = " ".join(summaries)

        return JsonResponse({
            "status": "success",
            "title": "Tóm tắt văn bản",
            "summary": final_summary
        }, json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        logger.error("⚠️ Lỗi JSON từ request!")
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        logger.exception(f"⚠️ Lỗi không xác định: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)