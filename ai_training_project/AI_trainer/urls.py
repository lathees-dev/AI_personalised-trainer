from django.urls import path
from . import views

app_name = "AI_trainer"

urlpatterns = [
    path("", views.home, name="home"),
    path("resume/", views.resume, name="resume"),
    path("video_resume/", views.upload_video, name="video_resume"),
    path("results/<int:resume_transcription_id>/", views.results, name="results"),
    path(
        "resume_form/", views.resume_form, name="resume_form"
    ),  # Renders the resume form page
    path("resume/save-user-info/", views.save_user_info, name="save_user_info"),
    path(
        "resume/fetch-latest-user-info/",
        views.fetch_latest_user_info,
        name="resume_preview",
    ),
    path("analyze-resume/", views.analyze_resume_view, name="analyze_resume"),
    path(
        "analysis/<int:analysis_id>/", views.display_analysis, name="display_analysis"
    ),
]
