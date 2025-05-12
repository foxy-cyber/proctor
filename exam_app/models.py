from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    is_student = models.BooleanField(default=False)
    is_administrator = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=100)
    usn = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Administrator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    admin_id = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.user.first_name
