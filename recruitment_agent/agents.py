import json
from mistralai import Mistral
from models import JobRequirements, CandidateProfile, CandidateScore


class DocumentAgent:
    """Extracts raw text from PDF files via Mistral OCR."""

    def __init__(self, client: Mistral):
        self.client = client

    def extract_text(self, file_path: str, file_name: str) -> str:
        try:
            with open(file_path, "rb") as f:
                uploaded_file = self.client.files.upload(
                    file={"file_name": file_name, "content": f},
                    purpose="ocr",
                )
            signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id)
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": signed_url.url},
            )
            return "\n\n".join(page.markdown for page in ocr_response.pages)
        except Exception as e:
            return f"[OCR error: {e}]"


class JobAnalysisAgent:
    """Parses a job description into a structured JobRequirements object."""

    def __init__(self, client: Mistral):
        self.client = client

    def extract_requirements(self, jd_text: str) -> dict:
        response = self.client.chat.parse(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "system",
                    "content": "Extract structured job requirements from the job description.",
                },
                {
                    "role": "user",
                    "content": f"Extract the key job requirements:\n\n{jd_text}",
                },
            ],
            response_format=JobRequirements,
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)


class ResumeAnalysisAgent:
    """Parses a resume into a structured CandidateProfile object."""

    def __init__(self, client: Mistral):
        self.client = client

    def extract_profile(self, resume_text: str) -> dict:
        response = self.client.chat.parse(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "system",
                    "content": "Extract structured candidate information from the resume.",
                },
                {
                    "role": "user",
                    "content": f"Extract the candidate's profile from the resume:\n\n{resume_text}",
                },
            ],
            response_format=CandidateProfile,
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)


class MatchingAgent:
    """Scores how well a candidate matches a job, returning a CandidateScore."""

    def __init__(self, client: Mistral):
        self.client = client

    def evaluate(self, job_requirements: dict, candidate_profile: dict) -> dict:
        prompt = f"""
Evaluate how well the candidate matches the job requirements.

Job Requirements:
{json.dumps(job_requirements, indent=2)}

Candidate Profile:
{json.dumps(candidate_profile, indent=2)}

Scoring breakdown:
- Technical skills  → max 40 pts
- Experience        → max 30 pts
- Education         → max 15 pts
- Additional        → max 15 pts
- Total             → max 100 pts

Assess quality and relevance, not just keyword matches. Include confidence levels.
"""
        response = self.client.chat.parse(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "system",
                    "content": "Evaluate the candidate's match to the job requirements with detailed scoring.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format=CandidateScore,
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
