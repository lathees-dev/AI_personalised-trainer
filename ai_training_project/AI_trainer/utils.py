import google.generativeai as genai
import PyPDF2
import json
import re
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def configure_genai(api_key: str) -> None:
    genai.configure(api_key=api_key)


def parse_pdf_resume(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")


def create_analysis_prompt(resume_text: str, job_description: str) -> str:
    return f"""
You are an ATS (Applicant Tracking System) and resume evaluator. Analyze the following resume against the provided job description and evaluate its various aspects based on the following criteria. Provide a detailed assessment and scores for each category. Ensure the response is structured strictly in JSON format as shown below.

---

#### Job Description:
{job_description}

#### Resume:
{resume_text}

---

Respond ONLY with a JSON object in the following format:

{{
    "ats_parse_rate": {{
        "score": 0,
        "reason": "string",
        "recommendations": "string",
        "pass": {{
            "passed": ["string"],
            "improve": ["string"]
        }}
    }},
    "contact_information": {{
        "score": 0,
        "reason": "string",
        "contact_links": {{
            "social_links": ["string"],
            "recommended": ["string"],
            "score": 0
        }}
    }},
    "skills_analysis": {{
        "hard_skills": {{
            "matched": ["string"],
            "not_suited": ["string"],
            "score": 0
        }},
        "soft_skills": {{
            "matched": ["string"],
            "not_suited": ["string"],
            "score": 0
        }},
        "reason": "string",
        "recommendations": "string"
    }},
    "description_quality": {{
        "score": 0,
        "reason": "string",
        "feedback": {{
            "strength": ["string"],
            "suggestions": ["string"]
        }}
    }},
    "experience_analysis": {{
        "years_of_experience": 0,
        "score": 0,
        "reason": "string",
        "details": {{
            "experience": ["string"],
            "improve": ["string"]
        }}
    }},
    "education_analysis": {{
        "score": 0,
        "reason": "string",
        "details": {{
            "background": ["string"],
            "suggest": ["string"]
        }}
    }},
    "projects_analysis": {{
        "score": 0,
        "reason": "string",
        "projects": {{
            "completed": ["string"],
            "suggested": ["string"]
        }}
    }},
    "overall_summary": {{
        "total_score": 0,
        "summary": "string",
        "over": {{
            "summary": ["string"],
            "improve": ["string"]
        }}
    }}
}}

Analyze the resume and provide scores and feedback in the exact format shown above. Ensure all fields are present and properly formatted.
"""


def extract_json_from_response(text: str) -> Dict:
    """Extract and validate JSON from response text."""
    try:
        # Try to parse the JSON
        result = json.loads(text)

        # Validate it's a dictionary
        if not isinstance(result, dict):
            raise ValueError(f"Expected dictionary, got {type(result)}")

        return result
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.error(f"Problematic text: {text}")
        raise


def clean_response_text(response_text: str) -> str:
    """Clean the response text to extract just the JSON content."""
    # Debug the input
    logger.debug(f"Input text to clean: {response_text}")
    
    # Remove any markdown code block markers
    text = response_text.strip()
    
    # If wrapped in code blocks, remove them
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    
    # Try to find JSON content between curly braces
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        text = text[start:end]
    except ValueError as e:
        logger.error(f"Error finding JSON structure: {str(e)}")
        logger.error(f"Text content: {text}")
        raise ValueError("Response does not contain valid JSON structure")
    
    # Clean up any remaining issues
    text = text.replace('\n', ' ').replace('\r', '')
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    
    logger.debug(f"Cleaned text output: {text}")
    return text


def analyze_resume(resume_text: str, job_description: str, api_key: str) -> Dict:
    try:
        configure_genai(api_key)
        model = genai.GenerativeModel("gemini-pro")

        # Step 1: Generate Prompt
        prompt = create_analysis_prompt(resume_text, job_description)
        
        # Configure generation parameters
        generation_config = {
            "temperature": 0.3,  # Lower temperature for more consistent output
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_DEROGATORY",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_TOXICITY",
                "threshold": "BLOCK_NONE",
            },
        ]
        
        # Generate response with specific configuration
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        # Debug logging
        logger.debug(f"Raw response type: {type(response)}")
        logger.debug(f"Raw response: {response}")
        logger.debug(f"Response text: {response.text}")

        # Step 2: Clean the Response
        cleaned_text = clean_response_text(response.text)
        logger.debug(f"Cleaned text: {cleaned_text}")

        # Step 3: Extract JSON
        try:
            # First attempt to parse the JSON
            analysis_result = json.loads(cleaned_text)
            
            # Ensure we have a dictionary
            if not isinstance(analysis_result, dict):
                logger.error(f"Unexpected result type: {type(analysis_result)}")
                logger.error(f"Result content: {analysis_result}")
                raise ValueError(f"Expected dictionary, got {type(analysis_result)}")

            # Validate Required Fields
            required_fields = [
                "ats_parse_rate",
                "contact_information",
                "skills_analysis",
                "description_quality",
                "experience_analysis",
                "education_analysis",
                "projects_analysis",
                "overall_summary",
            ]

            missing_fields = [field for field in required_fields if field not in analysis_result]
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Step 4: Return Analysis
            return analysis_result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Problematic text: {cleaned_text}")
            # Try to fix common JSON issues
            fixed_text = cleaned_text.replace("'", '"').replace("\n", " ")
            try:
                return json.loads(fixed_text)
            except:
                raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        logger.error(f"Full error details: ", exc_info=True)
        raise Exception(f"Error during analysis: {str(e)}")
