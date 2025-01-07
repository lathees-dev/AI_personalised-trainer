from django.db import models

class TrainingSession(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Transcription(models.Model):
    video_file = models.FileField(upload_to="videos/")
    transcription_text = models.TextField(null=True, blank=True)
    evaluation_result = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class UserInfo(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    social_links = models.TextField(blank=True)  # Store comma-separated
    professional_summary = models.TextField(blank=True)
    skills = models.TextField(blank=True)  # Comma-separated
    certifications = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    languages = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    fresher_or_professional = models.CharField(max_length=20)

    def __str__(self):
        return self.full_name
