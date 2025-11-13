"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ResumeTemplate(str, Enum):
    """Available resume templates"""
    MODERN = "modern"
    PROFESSIONAL = "professional"
    ATS_OPTIMIZED = "ats-optimized"
    EXECUTIVE = "executive"


class ImprovementType(str, Enum):
    """Types of improvements"""
    BULLET_POINT = "bullet_point"
    SUMMARY = "summary"
    KEYWORD = "keyword"
    ACHIEVEMENT = "achievement"
    GRAMMAR = "grammar"
    FORMATTING = "formatting"


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionPriority(str, Enum):
    """Suggestion priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Request Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request to analyze a resume"""
    resume_url: str = Field(..., description="URL to the resume file in storage")
    user_id: Optional[str] = Field(None, description="User ID for tracking")
    resume_improvement_id: Optional[str] = Field(None, description="Resume improvement session ID")

    class Config:
        json_schema_extra = {
            "example": {
                "resume_url": "https://storage.supabase.co/resumes/user123/resume.pdf",
                "user_id": "user123",
                "resume_improvement_id": "improvement123"
            }
        }


class ImproveRequest(BaseModel):
    """Request to get AI-powered improvements"""
    resume_improvement_id: str = Field(..., description="Resume improvement session ID")
    content: Dict[str, Any] = Field(..., description="Parsed resume content")
    focus_areas: Optional[List[str]] = Field(
        default=["bullet_points", "summary", "keywords"],
        description="Areas to focus on for improvements"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resume_improvement_id": "improvement123",
                "content": {
                    "summary": "Virtual assistant with 5 years experience",
                    "experience": [
                        {
                            "title": "Virtual Assistant",
                            "company": "Tech Corp",
                            "bullets": ["Managed calendars", "Handled emails"]
                        }
                    ]
                },
                "focus_areas": ["bullet_points", "summary"]
            }
        }


class GenerateRequest(BaseModel):
    """Request to generate improved resume PDF"""
    resume_improvement_id: str = Field(..., description="Resume improvement session ID")
    template: ResumeTemplate = Field(..., description="Template to use")
    content: Dict[str, Any] = Field(..., description="Improved resume content")
    user_id: str = Field(..., description="User ID for storage path")

    class Config:
        json_schema_extra = {
            "example": {
                "resume_improvement_id": "improvement123",
                "template": "modern",
                "content": {
                    "contact": {"name": "John Doe", "email": "john@example.com"},
                    "summary": "Experienced VA...",
                    "experience": [],
                    "education": [],
                    "skills": []
                },
                "user_id": "user123"
            }
        }


# ============================================================================
# Response Models
# ============================================================================

class ScoreBreakdown(BaseModel):
    """Scoring breakdown by category"""
    overall_score: float = Field(..., ge=0, le=100, description="Overall score out of 100")
    formatting_score: float = Field(..., ge=0, le=20, description="Formatting score out of 20")
    content_quality_score: float = Field(..., ge=0, le=30, description="Content quality score out of 30")
    ats_optimization_score: float = Field(..., ge=0, le=25, description="ATS optimization score out of 25")
    skills_section_score: float = Field(..., ge=0, le=15, description="Skills section score out of 15")
    professional_summary_score: float = Field(..., ge=0, le=10, description="Professional summary score out of 10")


class Issue(BaseModel):
    """A detected issue in the resume"""
    category: str = Field(..., description="Category of issue (formatting, content, ats, skills, summary)")
    severity: IssueSeverity = Field(..., description="Severity level")
    issue: str = Field(..., description="Description of the issue")
    location: Optional[str] = Field(None, description="Where in the resume (section name)")
    example: Optional[str] = Field(None, description="Example of the issue")


class Suggestion(BaseModel):
    """An improvement suggestion"""
    category: str = Field(..., description="Category of suggestion")
    priority: SuggestionPriority = Field(..., description="Priority level")
    suggestion: str = Field(..., description="The suggestion text")
    examples: Optional[List[str]] = Field(default=[], description="Example implementations")
    reasoning: Optional[str] = Field(None, description="Why this matters")


class AnalysisMetadata(BaseModel):
    """Metadata about the analyzed resume"""
    word_count: int
    page_count: int
    sections_found: List[str]
    has_action_verbs: bool
    has_quantifiable_achievements: bool
    keyword_density: Dict[str, int]


class AnalyzeResponse(BaseModel):
    """Response from resume analysis"""
    success: bool = True
    resume_improvement_id: str
    scores: ScoreBreakdown
    issues: List[Issue]
    suggestions: List[Suggestion]
    metadata: AnalysisMetadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "resume_improvement_id": "improvement123",
                "scores": {
                    "overall_score": 72.5,
                    "formatting_score": 15.0,
                    "content_quality_score": 20.0,
                    "ats_optimization_score": 18.5,
                    "skills_section_score": 12.0,
                    "professional_summary_score": 7.0
                },
                "issues": [
                    {
                        "category": "content",
                        "severity": "high",
                        "issue": "Bullet points lack quantifiable achievements",
                        "location": "Experience section"
                    }
                ],
                "suggestions": [
                    {
                        "category": "content",
                        "priority": "high",
                        "suggestion": "Add metrics to demonstrate impact",
                        "examples": ["Increased efficiency by 30%"]
                    }
                ],
                "metadata": {
                    "word_count": 450,
                    "page_count": 1,
                    "sections_found": ["contact", "summary", "experience", "education", "skills"],
                    "has_action_verbs": True,
                    "has_quantifiable_achievements": False,
                    "keyword_density": {"calendar management": 2, "email": 3}
                },
                "analyzed_at": "2025-01-12T10:00:00Z"
            }
        }


class Improvement(BaseModel):
    """An AI-generated improvement"""
    type: ImprovementType
    original: str
    improved: str
    section: str
    reasoning: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")


class ImproveResponse(BaseModel):
    """Response from improvement service"""
    success: bool = True
    resume_improvement_id: str
    improvements: List[Improvement]
    total_improvements: int
    estimated_score_increase: float = Field(..., description="Expected score increase if applied")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "resume_improvement_id": "improvement123",
                "improvements": [
                    {
                        "type": "bullet_point",
                        "original": "Managed calendars",
                        "improved": "Coordinated complex executive calendars for 5 C-suite leaders, optimizing scheduling efficiency by 40%",
                        "section": "experience",
                        "reasoning": "Added specificity and quantifiable impact",
                        "confidence": 0.95
                    }
                ],
                "total_improvements": 1,
                "estimated_score_increase": 8.5
            }
        }


class TemplateInfo(BaseModel):
    """Information about a resume template"""
    id: ResumeTemplate
    name: str
    description: str
    best_for: List[str]
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class TemplatesResponse(BaseModel):
    """Response with available templates"""
    success: bool = True
    templates: List[TemplateInfo]


class GenerateResponse(BaseModel):
    """Response from PDF generation"""
    success: bool = True
    resume_improvement_id: str
    template: ResumeTemplate
    file_url: str = Field(..., description="URL to download the generated PDF")
    file_name: str
    file_size: int = Field(..., description="File size in bytes")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "resume_improvement_id": "improvement123",
                "template": "modern",
                "file_url": "https://storage.supabase.co/resume-improvements/user123/improved-resume.pdf",
                "file_name": "John_Doe_Resume_Improved.pdf",
                "file_size": 245760,
                "generated_at": "2025-01-12T10:05:00Z"
            }
        }


# ============================================================================
# Error Response
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    message: str
    details: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
