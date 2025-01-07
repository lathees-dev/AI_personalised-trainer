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
