from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Transcription
from .models import UserInfo
import google.generativeai as genai
from pymongo import MongoClient
import os
import ffmpeg
import whisper
import json
import logging

logger = logging.getLogger(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["AI_trainer"]
collection = db["ATS_Resume"]


genai.configure(api_key="AIzaSyDB5eH-ldf8haalnbOVoDAdYqZnb_IBpRk")

def home(request):
    """Renders the home page."""
    return render(request, 'AI_trainer/home.html')

# Resume Section starts here
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


def resume_form(request):
    return render(request, "AI_trainer/resumeForm.html")


# Assuming Resume is a model in models.py

@csrf_exempt
def save_user_info(request):
    if request.method == "POST":
        try:
            

            # Extract data using request.POST (this handles form data correctly)
            email = request.POST.get('personalInfo[email]', '')
            full_name = request.POST.get('personalInfo[name]', '')
            phone = request.POST.get('personalInfo[phone]', '')
            address = request.POST.get('personalInfo[address]', '')
            social_links = request.POST.get('socialLinks', '').split(',')  # split by commas
            professional_summary = request.POST.get('professionalSummary', '')
            skills = request.POST.get('skills', '').split(',')  # split by commas
            certifications = request.POST.get('certifications', '').split(',')  # split by commas
            achievements = request.POST.get('achievements', '').split(',')  # split by commas
            languages = request.POST.get('languages', '').split(',')  # split by commas
            projects = request.POST.get('projects', '').split(',')  # split by commas
            experience = request.POST.get('experience', '').split(',')  # split by commas
            fresher_or_professional = request.POST.get('fresher_or_professional', '')


            # Save data in the database
            user_info = {
                "email": email,
                "full_name": full_name,
                "phone": phone,
                "address": address,
                "social_links": social_links,  # Directly store the list, MongoDB supports arrays
                "professional_summary": professional_summary,
                "skills": skills,  # Directly store the list
                "certifications": certifications,  # Directly store the list
                "achievements": achievements,  # Directly store the list
                "languages": languages,  # Directly store the list
                "projects": projects,  # Directly store the list
                "experience": experience,  # Directly store the list
                "fresher_or_professional": fresher_or_professional,
            }
            # Insert data into MongoDB collection
            collection.insert_one(user_info)  # Insert the user data as a document

            return redirect('AI_trainer:resume_preview')

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)


def fetch_latest_user_info(request):
    try:
        # Get the latest user info, ordered by last modification
        latest_user = collection.find().sort("last_modified", -1).limit(1)

        latest_user = list(latest_user)
        if not latest_user:
            return JsonResponse({"error": "No user data found"}, status=404)

        latest_user = latest_user[0]  # Fetch the first record in the list

        # Decode social_links JSON string to a dictionary
        social_links = latest_user.get("social_links", {})
        # Prepare user data for the response
        user_data = {
            "personal_info": {
                "name": latest_user.get("full_name", ""),
                "email": latest_user.get("email", ""),
                "phone": latest_user.get("phone", ""),
                "address": latest_user.get("address", ""),
            },
            "professional_summary": latest_user.get("professional_summary", ""),
            "social_links": {
                "linkedIn": social_links[0] if len(social_links) > 0 else "",
                "github": social_links[1] if len(social_links) > 1 else "",
                "twitter": social_links[2] if len(social_links) > 2 else "",
            },
            "education": latest_user.get("education", []),
            "skills": latest_user.get("skills", []),
            "certifications": latest_user.get("certifications", []),
            "achievements": latest_user.get("achievements", []),
            "languages": latest_user.get("languages", []),
            "projects": latest_user.get("projects", []),
            "experience": latest_user.get("experience", []),
        }

        # logger.debug("User Data being returned: %s", user_data)
        return render(request, 'AI_trainer/resumePreview.html', {'user_data': user_data})

    except Exception as e:
        logger.exception("Failed to fetch user info: %s", str(e))
        return JsonResponse({"error": str(e)}, status=500)
