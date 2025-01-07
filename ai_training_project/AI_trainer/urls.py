from django.urls import path
from . import views

app_name = 'AI_trainer'

urlpatterns = [
    path("", views.home, name="home"),
    path("resume/", views.resume, name="resume"),
    path("video_resume/", views.upload_video, name="video_resume"),
    path(
        "results/<int:resume_transcription_id>/",
        views.results,
        name="results",
    ),
]
