from django import forms
from .models import ResumeAnalysis


class VideoForm(forms.Form):
    intro_video = forms.FileField(label="Upload your Self Introduction Video")
    resume_video = forms.FileField(label="Upload your Resume Video")


class ResumeAnalysisForm(forms.ModelForm):

    class Meta:

        model = ResumeAnalysis

        fields = ["resume_file", "job_description"]

        widgets = {
            "resume_file": forms.FileInput(
                attrs={"accept": ".pdf", "class": "hidden", "id": "id_resume_file"}
            ),
            "job_description": forms.Textarea(
                attrs={
                    "placeholder": "Paste the job description here...",
                    "rows": 6,
                    "class": "form-textarea",
                }
            ),
        }
