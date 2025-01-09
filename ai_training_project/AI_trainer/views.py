
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Transcription
from .models import UserInfo
import google.generativeai as genai
from pymongo import MongoClient
import os
import ffmpeg
import whisper
import json
import logging
from django.conf import settings
import PyPDF2
import io
from .utils import parse_pdf_resume, analyze_resume
from .forms import ResumeAnalysisForm
from .models import ResumeAnalysis

logger = logging.getLogger(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["AI_trainer"]
collection = db["ATS_Resume"]


genai.configure(api_key="AIzaSyDB5eH-ldf8haalnbOVoDAdYqZnb_IBpRk")


def home(request):
    """Renders the home page."""
    return render(request, "AI_trainer/home.html")


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
    skills_options = [
        {"value": "JavaScript", "label": "JavaScript"},
        {"value": "Python", "label": "Python"},
        {"value": "React", "label": "React"},
        # ... add all skills from the React version
    ]
    return render(
        request, "AI_trainer/resumeForm.html", {"skills_options": skills_options}
    )


# Assuming Resume is a model in models.py


@csrf_exempt
def save_user_info(request):
    if request.method == "POST":
        try:
            data = request.POST.dict()

            # Process arrays from form data
            education = []
            experience = []
            certifications = []
            languages = []
            projects = []

            # Process all form fields
            for key, value in data.items():
                if key.startswith("education["):
                    parts = key.split("].")
                    index = int(parts[0].split("[")[1])
                    field = parts[1]
                    while len(education) <= index:
                        education.append({})
                    education[index][field] = value
                elif key.startswith("experience["):
                    parts = key.split("].")
                    index = int(parts[0].split("[")[1])
                    field = parts[1]
                    while len(experience) <= index:
                        experience.append({})
                    experience[index][field] = value
                elif key.startswith("certifications["):
                    parts = key.split("].")
                    index = int(parts[0].split("[")[1])
                    field = parts[1]
                    while len(certifications) <= index:
                        certifications.append({})
                    certifications[index][field] = value
                elif key.startswith("languages["):
                    parts = key.split("].")
                    index = int(parts[0].split("[")[1])
                    field = parts[1]
                    while len(languages) <= index:
                        languages.append({})
                    languages[index][field] = value
                elif key.startswith("projects["):
                    parts = key.split("].")
                    index = int(parts[0].split("[")[1])
                    field = parts[1]
                    while len(projects) <= index:
                        projects.append({})
                    projects[index][field] = value

            user_info = {
                "email": data.get("personalInfo.email"),
                "full_name": data.get("personalInfo.name"),
                "phone": data.get("personalInfo.phone"),
                "address": data.get("personalInfo.address"),
                "social_links": {
                    "linkedIn": data.get("socialLinks.linkedIn"),
                    "github": data.get("socialLinks.github"),
                    "twitter": data.get("socialLinks.twitter"),
                },
                "professional_summary": data.get("professionalSummary"),
                "education": [edu for edu in education if edu],
                "skills": request.POST.getlist("skills"),
                "certifications": [cert for cert in certifications if cert],
                "languages": [lang for lang in languages if lang],
                "experience": [exp for exp in experience if exp],
                "projects": [proj for proj in projects if proj],
            }

            collection.insert_one(user_info)
            return redirect("AI_trainer:resume_preview")

        except Exception as e:
            logger.error(f"Error saving user info: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def fetch_latest_user_info(request):
    try:
        latest_user = collection.find().sort("_id", -1).limit(1)
        latest_user = list(latest_user)

        if not latest_user:
            return render(
                request,
                "AI_trainer/ResumePreview.html",
                {"user_data": None, "error": "No user data found"},
            )

        latest_user = latest_user[0]

        # Format the data structure to match the template
        user_data = {
            "personalInfo": {
                "name": latest_user.get("full_name"),
                "email": latest_user.get("email"),
                "phone": latest_user.get("phone", ""),
                "address": latest_user.get("address", ""),
            },
            "social_links": latest_user.get("social_links", {}),
            "professional_summary": latest_user.get("professional_summary", ""),
            "education": latest_user.get("education", []),
            "experience": latest_user.get("experience", []),
            "skills": latest_user.get("skills", []),
            "certifications": latest_user.get("certifications", []),
            "languages": latest_user.get("languages", []),
            "projects": latest_user.get("projects", []),
            "achievements": latest_user.get("achievements", []),
        }

        print("Debug - User Data:", user_data)  # Add this for debugging

        return render(
            request,
            "AI_trainer/ResumePreview.html",
            {"user_data": user_data, "error": None},
        )

    except Exception as e:
        logger.error(f"Error in fetch_latest_user_info: {str(e)}", exc_info=True)
        return render(
            request,
            "AI_trainer/ResumePreview.html",
            {"user_data": None, "error": str(e)},
        )


def resume_preview(request):
    try:
        # Get the latest user info from MongoDB
        latest_user = collection.find().sort("last_modified", -1).limit(1)
        latest_user = list(latest_user)

        if not latest_user:
            return render(
                request,
                "AI_trainer/ResumePreview.html",
                {"loading": False, "error": "No user data found", "user_data": None},
            )

        latest_user = latest_user[0]  # Get the first document

        # Format the data for the template
        user_data = {
            "personalInfo": {
                "name": latest_user.get("full_name", ""),
                "email": latest_user.get("email", ""),
                "phone": latest_user.get("phone", ""),
                "address": latest_user.get("address", ""),
            },
            "professional_summary": latest_user.get("professional_summary", ""),
            "socialLinks": {
                "linkedIn": (
                    latest_user.get("social_links", [])[0]
                    if latest_user.get("social_links")
                    else ""
                ),
                "github": (
                    latest_user.get("social_links", [])[1]
                    if latest_user.get("social_links")
                    and len(latest_user.get("social_links")) > 1
                    else ""
                ),
                "twitter": (
                    latest_user.get("social_links", [])[2]
                    if latest_user.get("social_links")
                    and len(latest_user.get("social_links")) > 2
                    else ""
                ),
            },
            "education": latest_user.get("education", []),
            "skills": latest_user.get("skills", []),
            "certifications": latest_user.get("certifications", []),
            "achievements": latest_user.get("achievements", []),
            "languages": latest_user.get("languages", []),
            "projects": latest_user.get("projects", []),
            "experience": latest_user.get("experience", []),
        }

        return render(
            request,
            "AI_trainer/ResumePreview.html",
            {"user_data": user_data, "loading": False, "error": None},
        )
    except Exception as e:
        logger.error(f"Error in resume_preview: {str(e)}", exc_info=True)
        return render(
            request,
            "AI_trainer/ResumePreview.html",
            {"loading": False, "error": str(e), "user_data": None},
        )


def parse_pdf_resume(pdf_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def analyze_resume(resume_text, job_description, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")

    prompt = f"""
    Analyze this resume against the job description and provide detailed feedback:

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Please provide analysis in the following format:
    1. Match Score (0-100)
    2. Key Strengths
    3. Missing Skills/Requirements
    4. Recommendations for Improvement
    5. Overall Assessment

    Be specific and actionable in your feedback.
    """

    response = model.generate_content(prompt)
    return response.text


@csrf_exempt
def analyze_resume_view(request):
    if request.method == "GET":
        return render(
            request, "AI_trainer/resume_analyzer.html", {"form": ResumeAnalysisForm()}
        )

    elif request.method == "POST":
        form = ResumeAnalysisForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                analysis = form.save(commit=False)
                resume_text = parse_pdf_resume(request.FILES["resume_file"])
                api_key = "AIzaSyDB5eH-ldf8haalnbOVoDAdYqZnb_IBpRk"
                analysis_result = analyze_resume(
                    resume_text, form.cleaned_data["job_description"], api_key
                )
                
                # Debug logging
                logger.debug(f"Analysis Result Type: {type(analysis_result)}")
                logger.debug(f"Analysis Result: {analysis_result}")
                
                # Ensure analysis_result is a dictionary before converting to JSON
                if not isinstance(analysis_result, dict):
                    raise ValueError("Analysis result is not a dictionary")
                
                # Store the analysis result as a JSON string
                analysis.analysis_result = json.dumps(analysis_result)
                analysis.save()
                
                logger.debug(f"Saved Analysis ID: {analysis.id}")

                # For AJAX requests, return JSON
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": True, "analysis": analysis_result})

                # For regular form submissions, redirect to analysis page
                return redirect("AI_trainer:display_analysis", analysis_id=analysis.id)

            except Exception as e:
                logger.error(f"Error in analyze_resume_view: {str(e)}")
                return JsonResponse({"error": str(e)}, status=500)
        else:
            return JsonResponse({"error": "Invalid form data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def resume_analyzer_page(request):
    form = ResumeAnalysisForm()
    return render(request, "AI_trainer/resume_analyzer.html", {"form": form})



def display_analysis(request, analysis_id):
    try:
        analysis = ResumeAnalysis.objects.get(id=analysis_id)
        
        # Debug logging
        logger.debug(f"Analysis Result Raw: {analysis.analysis_result}")
        
        try:
            # Convert the stored JSON string to a dictionary
            analysis_data = json.loads(analysis.analysis_result)
            
            # Validate required fields
            required_fields = [
                "ats_parse_rate", "contact_information", "skills_analysis",
                "description_quality", "experience_analysis", "education_analysis",
                "projects_analysis"
            ]
            
            for field in required_fields:
                if field not in analysis_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Debug logging
            logger.debug(f"Analysis Data: {analysis_data}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {str(e)}")
            return HttpResponse(f"Invalid analysis data format: {str(e)}", status=500)
        except ValueError as e:
            logger.error(f"Validation Error: {str(e)}")
            return HttpResponse(f"Invalid analysis data structure: {str(e)}", status=500)
        
        # Transform analysis data into sections format
        sections = [
            {
                "id": "ats",
                "title": "ATS Compatibility",
                "icon_html": '<i class="fas fa-robot"></i>',
                "score": analysis_data["ats_parse_rate"]["score"],
                "details": {
                    "strengthsHeading": "ATS Strengths",
                    "improvementsHeading": "ATS Improvements",
                    "strengths": analysis_data["ats_parse_rate"]["pass"]["passed"],
                    "improvements": analysis_data["ats_parse_rate"]["pass"]["improve"],
                    "feedback": {
                        "overview": analysis_data["ats_parse_rate"]["reason"],
                        "recommendations": analysis_data["ats_parse_rate"][
                            "recommendations"
                        ],
                        "impact": "ATS compatibility affects your resume's visibility",
                    },
                },
            },
            {
                "id": "contact",
                "title": "Contact Information",
                "icon_html": '<i class="fas fa-address-card"></i>',
                "score": analysis_data["contact_information"]["contact_links"]["score"],
                "details": {
                    "strengthsHeading": "Available Links",
                    "improvementsHeading": "Recommended Links",
                    "strengths": analysis_data["contact_information"]["contact_links"][
                        "social_links"
                    ],
                    "improvements": analysis_data["contact_information"][
                        "contact_links"
                    ]["recommended"],
                    "feedback": {
                        "overview": analysis_data["contact_information"]["reason"],
                        "recommendations": "Ensure professional contact details are clear",
                        "impact": "Professional networking enhances visibility",
                    },
                },
            },
            {
                "id": "skills",
                "title": "Skills Analysis",
                "icon_html": '<i class="fas fa-code"></i>',
                "score": analysis_data["skills_analysis"]["hard_skills"]["score"],
                "details": {
                    "strengthsHeading": "Matched Skills",
                    "improvementsHeading": "Missing Skills",
                    "strengths": analysis_data["skills_analysis"]["hard_skills"][
                        "matched"
                    ],
                    "improvements": analysis_data["skills_analysis"]["hard_skills"][
                        "not_suited"
                    ],
                    "feedback": {
                        "overview": analysis_data["skills_analysis"]["reason"],
                        "recommendations": analysis_data["skills_analysis"][
                            "recommendations"
                        ],
                        "impact": "Skills match is crucial for job fit",
                    },
                },
            },
            {
                "id": "description",
                "title": "Description Quality",
                "icon_html": '<i class="fas fa-file-alt"></i>',
                "score": analysis_data["description_quality"]["score"],
                "details": {
                    "strengthsHeading": "Content Strengths",
                    "improvementsHeading": "Areas to Improve",
                    "strengths": analysis_data["description_quality"]["feedback"][
                        "strength"
                    ],
                    "improvements": analysis_data["description_quality"]["feedback"][
                        "suggestions"
                    ],
                    "feedback": {
                        "overview": analysis_data["description_quality"]["reason"],
                        "recommendations": "Focus on clarity and impact",
                        "impact": "Clear descriptions improve understanding",
                    },
                },
            },
            {
                "id": "experience",
                "title": "Experience Analysis",
                "icon_html": '<i class="fas fa-briefcase"></i>',
                "score": analysis_data["experience_analysis"]["score"],
                "details": {
                    "strengthsHeading": "Experience Highlights",
                    "improvementsHeading": "Areas to Enhance",
                    "strengths": analysis_data["experience_analysis"]["details"][
                        "experience"
                    ],
                    "improvements": analysis_data["experience_analysis"]["details"][
                        "improve"
                    ],
                    "feedback": {
                        "overview": analysis_data["experience_analysis"]["reason"],
                        "recommendations": "Highlight relevant experience",
                        "impact": "Experience demonstrates practical skills",
                    },
                },
            },
            {
                "id": "education",
                "title": "Education Analysis",
                "icon_html": '<i class="fas fa-graduation-cap"></i>',
                "score": analysis_data["education_analysis"]["score"],
                "details": {
                    "strengthsHeading": "Educational Background",
                    "improvementsHeading": "Recommended Courses",
                    "strengths": analysis_data["education_analysis"]["details"][
                        "background"
                    ],
                    "improvements": analysis_data["education_analysis"]["details"][
                        "suggest"
                    ],
                    "feedback": {
                        "overview": analysis_data["education_analysis"]["reason"],
                        "recommendations": "Consider additional certifications",
                        "impact": "Education provides foundational knowledge",
                    },
                },
            },
            {
                "id": "projects",
                "title": "Projects Analysis",
                "icon_html": '<i class="fas fa-project-diagram"></i>',
                "score": analysis_data["projects_analysis"]["score"],
                "details": {
                    "strengthsHeading": "Completed Projects",
                    "improvementsHeading": "Suggested Projects",
                    "strengths": analysis_data["projects_analysis"]["projects"][
                        "completed"
                    ],
                    "improvements": analysis_data["projects_analysis"]["projects"][
                        "suggested"
                    ],
                    "feedback": {
                        "overview": analysis_data["projects_analysis"]["reason"],
                        "recommendations": "Add relevant projects",
                        "impact": "Projects showcase practical application",
                    },
                },
            },
        ]
        
        context = {
            "analysis": analysis_data,
            "sections": sections,
        }
        
        # Debug logging
        logger.debug(f"Rendering template with context: {context}")
        
        return render(
            request,
            "AI_trainer/resume_analysis.html",
            context
        )
        
    except ResumeAnalysis.DoesNotExist:
        logger.error(f"Analysis not found: {analysis_id}")
        return HttpResponse("Analysis not found", status=404)
    except Exception as e:
        logger.error(f"Unexpected error in display_analysis: {str(e)}")
        return HttpResponse(f"Error processing analysis: {str(e)}", status=500)
