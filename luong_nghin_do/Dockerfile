# Sử dụng Python 3.12
FROM python:3.12

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements.txt vào container trước
COPY requirements.txt .

# Cài đặt các thư viện từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project vào container
COPY . .

# Chạy server Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]