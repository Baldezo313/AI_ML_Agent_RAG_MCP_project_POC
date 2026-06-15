from typing import List, Optional
from pydantic import BaseModel, Field


class Skill(BaseModel):
    name: str = Field(description="Name of the skill or technology")
    level: Optional[str] = Field(default=None, description="Proficiency level")
    year: Optional[float] = Field(default=None, description="Years of experience")


class Education(BaseModel):
    degree: str
    field: str
    institution: str
    year_completed: Optional[int] = None
    gpa: Optional[float] = None


class Experience(BaseModel):
    title: str
    company: str
    duration_years: float
    skills_used: List[str]
    achievements: List[str]
    relevance_score: Optional[float] = None


class ContactDetails(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None


class JobRequirements(BaseModel):
    required_skills: List[Skill]
    preferred_skills: List[Skill]
    min_experience_years: float
    required_education: List[Education]
    preferred_domains: List[str]


class CandidateProfile(BaseModel):
    contact_details: ContactDetails
    skills: List[Skill]
    education: List[Education]
    experience: List[Experience]


class CandidateScore(BaseModel):
    technical_skills_score: float
    experience_score: float
    education_score: float
    additional_score: float
    total_score: float
    key_strengths: List[str]
    key_gaps: List[str]
    confidence: float
    notes: str
