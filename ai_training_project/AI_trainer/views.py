from django.shortcuts import render
from .models import TrainingSession


from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
import os
import ffmpeg
import whisper
import google.generativeai as genai
from .models import Transcription

genai.configure(api_key="AIzaSyDB5eH-ldf8haalnbOVoDAdYqZnb_IBpRk")

def home(request):
    """Renders the home page."""
    return render(request, 'AI_trainer/home.html')


def resume(request):
    """Renders the home page."""
    return render(request, "AI_trainer/resume.html")


def convert_mp4_to_wav(input_file, output_file):
    try:
        ffmpeg.input(input_file).output(output_file).run(overwrite_output=True)
        return True
    except Exception as e:
        return False


def transcribe_audio(input_file):
    # Transcribe the audio file
    model = whisper.load_model("base.en")
    result = model.transcribe(input_file)
    return result["text"]


def upload_video(request):
    if request.method == "POST":
        # Check if the video resume file is provided
        if "video_resume" in request.FILES:
            video_resume = request.FILES["video_resume"]

            # Create a transcription entry for the video resume
            resume_transcription = Transcription.objects.create(video_file=video_resume)

            # Process video resume
            resume_video_path = resume_transcription.video_file.path
            resume_wav_path = f"{os.path.splitext(resume_video_path)[0]}.wav"

            if not convert_mp4_to_wav(resume_video_path, resume_wav_path):
                return render(
                    request,
                    "AI_trainer/VR_upload.html",
                    {"error": "Video resume conversion failed."},
                )

            resume_transcription_text = transcribe_audio(resume_wav_path)
            resume_transcription.transcription_text = resume_transcription_text
            resume_transcription.save()

            # Redirect to results page for the video resume transcription
            return redirect(
                "AI_trainer:results",
                resume_transcription_id=resume_transcription.id,
            )

        else:
            return render(
                request,
                "AI_trainer/VR_upload.html",
                {"error": "Please upload the video resume."},
            )

    return render(request, "AI_trainer/VR_upload.html")


def evaluate_transcription(transcription):

    prompt = f"""
        Please evaluate the following Video Resume transcription based on these criteria:

1. Professional Impact:

-How well does the candidate convey their professional experience, skills, and achievements?
-Is there a compelling narrative that showcases their value proposition effectively?

2.Relevance to Target Role:
-Are the discussed experiences and skills highly relevant to the assumed job role or industry?
-Does the candidate demonstrate alignment with the potential employer's needs?

3.Clarity and Articulation:
-How clear and concise is the candidate’s communication? Are their ideas logically presented and easy to follow?

4.Delivery and Enthusiasm:
-How confident and enthusiastic is the candidate in their delivery? Does their tone and pace maintain engagement?

5.Storytelling Ability:
-How well does the candidate weave their experiences into a cohesive and memorable story? Are their achievements narrated effectively?

6.Grammar, Syntax, and Presentation:

-Is the language grammatically correct and polished? Are there noticeable errors or awkward phrasing?

Provide Output in the Following Format:
Category-wise Scores and Reasoning:

1. Professional Impact:

Score: X/10
Reasoning: [Detailed evaluation]
2. Relevance to Target Role:

Score: X/10
Reasoning: [Detailed evaluation]
3. Clarity and Articulation:

Score: X/10
Reasoning: [Detailed evaluation]
4. Delivery and Enthusiasm:

Score: X/10
Reasoning: [Detailed evaluation]
5. Storytelling Ability:

Score: X/10
Reasoning: [Detailed evaluation]
6. Grammar, Syntax, and Presentation:

Score: X/10
Reasoning: [Detailed evaluation]
Overall Summary:

Total Score: X/60
Feedback:
Overall feedback summary based on the evaluation.
Strengths: [Key strengths identified in the transcription]
Areas for Improvement: [Detailed suggestions for improvement]
Below is the transcription to evaluate:

{transcription}
        """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    clean_response = response.text.replace("*", "").replace("#", "").strip()

    return clean_response


def results(request, resume_transcription_id):
    resume_transcription = Transcription.objects.get(id=resume_transcription_id)

    # Evaluate video resume transcription
    if not resume_transcription.evaluation_result:
        resume_transcription.evaluation_result = evaluate_transcription(
            resume_transcription.transcription_text
        )
        resume_transcription.save()

    return render(
        request,
        "AI_trainer/VR_results.html",
        {
            "transcription_other": resume_transcription.transcription_text,
            "evaluation_other": resume_transcription.evaluation_result,
        },
    )
