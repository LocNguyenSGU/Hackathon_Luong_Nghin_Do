from django.db import models
import cloudinary
import cloudinary.models
class UserDetail(models.Model):
    idUser = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    google_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.email

class ChuDe(models.Model):
    id = models.AutoField(primary_key=True)
    name_chu_de = models.CharField(max_length=255)
    noi_dung = models.TextField()

    def __str__(self):
        return self.name_chu_de

class File(models.Model):
    idFile = models.AutoField(primary_key=True)
    url = models.URLField()
    type = models.CharField(max_length=50, choices=[('image', 'Image'), ('docx', 'DOCX')])
    isInput = models.BooleanField(default=False)
    idChuDe = models.ForeignKey(ChuDe, on_delete=models.CASCADE)
    idUser = models.ForeignKey(UserDetail, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.type} - {self.url}"

class DanhGia(models.Model):
    id = models.AutoField(primary_key=True)
    idChuDe = models.ForeignKey(ChuDe, on_delete=models.CASCADE)
    idUser = models.ForeignKey(UserDetail, on_delete=models.CASCADE)
    idThread = models.CharField(max_length=255, unique=True, null=True, blank=True) 
    nhan_xet = models.TextField()

    def __str__(self):
        return f"Đánh giá từ {self.idUser} về {self.idChuDe}"
class ImageUpload(models.Model):
    image = cloudinary.models.CloudinaryField('image')
    uploaded_at = models.DateTimeField(auto_now_add=True)
