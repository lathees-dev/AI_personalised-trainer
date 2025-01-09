from django import forms


class VideoForm(forms.Form):
    intro_video = forms.FileField(label="Upload your Self Introduction Video")
    resume_video = forms.FileField(label="Upload your Resume Video")
