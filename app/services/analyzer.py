"""
Resume Analyzer Service
Handles resume scoring and analysis across 5 categories
"""
from typing import Optional, List, Dict, Any, Tuple
import logging
import re
from datetime import datetime
import httpx
from app.models.schemas import (
    AnalyzeResponse, ScoreBreakdown, Issue, Suggestion,
    AnalysisMetadata, IssueSeverity, SuggestionPriority
)
from app.utils.config import get_settings

logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    """
    Analyzes resumes and provides scoring across 5 categories:
    1. Formatting (20 points)
    2. Content Quality (30 points)
    3. ATS Optimization (25 points)
    4. Skills Section (15 points)
    5. Professional Summary (10 points)
    """

    # VA-specific keywords for optimization scoring
    VA_KEYWORDS = [
        'virtual assistant', 'administrative support', 'calendar management',
        'email management', 'scheduling', 'data entry', 'crm', 'customer service',
        'project coordination', 'travel coordination', 'expense management',
        'social media', 'content management', 'bookkeeping', 'invoicing',
        'asana', 'trello', 'monday.com', 'slack', 'zoom', 'google workspace',
        'microsoft office', 'excel', 'powerpoint', 'ghl', 'gohighlevel'
    ]

    # Strong action verbs for content scoring
    ACTION_VERBS = [
        'managed', 'coordinated', 'led', 'developed', 'implemented', 'optimized',
        'streamlined', 'organized', 'executed', 'facilitated', 'achieved',
        'increased', 'reduced', 'improved', 'created', 'designed', 'established',
        'maintained', 'analyzed', 'processed', 'handled', 'supported', 'assisted'
    ]

    def __init__(self, nlp_model=None):
        """
        Initialize analyzer with NLP model

        Args:
            nlp_model: spaCy NLP model for text analysis
        """
        self.nlp = nlp_model
        self.settings = get_settings()
        logger.info("ResumeAnalyzer initialized")

    async def analyze(
        self,
        resume_url: str,
        user_id: Optional[str] = None,
        resume_improvement_id: Optional[str] = None
    ) -> AnalyzeResponse:
        """
        Perform complete resume analysis

        Args:
            resume_url: URL to resume file in storage
            user_id: Optional user ID
            resume_improvement_id: Optional session ID

        Returns:
            AnalyzeResponse with scores, issues, suggestions, and metadata
        """
        logger.info(f"Analyzing resume: {resume_url}")

        try:
            # Parse resume from URL using Railway parser
            parsed_content = await self._parse_resume(resume_url, user_id)

            # Calculate scores for each category
            all_issues: List[Issue] = []

            formatting_score, formatting_issues = self._score_formatting(parsed_content)
            all_issues.extend(formatting_issues)

            content_score, content_issues = self._score_content_quality(parsed_content)
            all_issues.extend(content_issues)

            ats_score, ats_issues = self._score_ats_optimization(parsed_content)
            all_issues.extend(ats_issues)

            skills_score, skills_issues = self._score_skills_section(parsed_content)
            all_issues.extend(skills_issues)

            summary_score, summary_issues = self._score_professional_summary(parsed_content)
            all_issues.extend(summary_issues)

            # Calculate overall score
            overall_score = (
                formatting_score + content_score + ats_score +
                skills_score + summary_score
            )

            # Generate suggestions based on issues
            suggestions = self._generate_suggestions(all_issues, parsed_content)

            # Extract metadata
            metadata = self._extract_metadata(parsed_content)

            return AnalyzeResponse(
                resume_improvement_id=resume_improvement_id or "generated-id",
                scores=ScoreBreakdown(
                    overall_score=overall_score,
                    formatting_score=formatting_score,
                    content_quality_score=content_score,
                    ats_optimization_score=ats_score,
                    skills_section_score=skills_score,
                    professional_summary_score=summary_score
                ),
                issues=all_issues,
                suggestions=suggestions,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            # Return a helpful error response instead of crashing
            raise

    def _create_mock_analysis(self, resume_improvement_id: str) -> AnalyzeResponse:
        """Create mock analysis response for testing"""
        return AnalyzeResponse(
            resume_improvement_id=resume_improvement_id,
            scores=ScoreBreakdown(
                overall_score=72.5,
                formatting_score=15.0,
                content_quality_score=20.0,
                ats_optimization_score=18.5,
                skills_section_score=12.0,
                professional_summary_score=7.0
            ),
            issues=[
                Issue(
                    category="content",
                    severity=IssueSeverity.HIGH,
                    issue="Bullet points lack quantifiable achievements",
                    location="Experience section",
                    example="'Managed calendars' should be 'Managed 10+ executive calendars, reducing scheduling conflicts by 40%'"
                ),
                Issue(
                    category="formatting",
                    severity=IssueSeverity.MEDIUM,
                    issue="Inconsistent date formats",
                    location="Experience section",
                    example="Mix of '2020-01' and 'Jan 2020' formats"
                ),
                Issue(
                    category="ats",
                    severity=IssueSeverity.CRITICAL,
                    issue="No contact information in standard format",
                    location="Header",
                    example="Email and phone should be clearly separated"
                )
            ],
            suggestions=[
                Suggestion(
                    category="content",
                    priority=SuggestionPriority.CRITICAL,
                    suggestion="Add quantifiable metrics to demonstrate impact",
                    examples=[
                        "Increased team productivity by 30%",
                        "Managed budget of $50K",
                        "Coordinated 15+ daily meetings"
                    ],
                    reasoning="Numbers and metrics make achievements concrete and impressive"
                ),
                Suggestion(
                    category="skills",
                    priority=SuggestionPriority.HIGH,
                    suggestion="Add more VA-specific software skills",
                    examples=[
                        "Calendar Management: Google Calendar, Outlook",
                        "Project Management: Asana, Monday.com, Trello",
                        "CRM: HubSpot, Salesforce, Pipedrive"
                    ],
                    reasoning="Specific tools demonstrate hands-on experience"
                ),
                Suggestion(
                    category="summary",
                    priority=SuggestionPriority.MEDIUM,
                    suggestion="Strengthen professional summary with value proposition",
                    examples=[
                        "Detail-oriented Virtual Assistant with 5+ years supporting C-suite executives",
                        "Specialized in calendar optimization, reducing scheduling conflicts by 40%"
                    ],
                    reasoning="Strong summary hooks recruiters and sets the tone"
                )
            ],
            metadata=AnalysisMetadata(
                word_count=450,
                page_count=1,
                sections_found=["contact", "summary", "experience", "education", "skills"],
                has_action_verbs=True,
                has_quantifiable_achievements=False,
                keyword_density={
                    "virtual assistant": 2,
                    "calendar management": 3,
                    "email": 2,
                    "administrative": 1
                }
            )
        )

    async def _parse_resume(self, resume_url: str, user_id: Optional[str]) -> Dict[str, Any]:
        """
        Parse resume content from URL using internal PyMuPDF parser

        Args:
            resume_url: Public URL to resume file
            user_id: Optional user ID for tracking

        Returns:
            Parsed resume content dictionary
        """
        from app.services.parser import ResumeParser

        parser = ResumeParser()
        parsed_data = await parser.parse_resume(resume_url, user_id)

        return parsed_data

    def _score_formatting(self, content: Dict) -> Tuple[float, List[Issue]]:
        """
        Score formatting (0-20 points)

        Checks:
        - Consistent date formats (5 pts)
        - Clear section headers (5 pts)
        - Proper spacing and structure (5 pts)
        - Optimal length 1-2 pages (5 pts)
        """
        score = 0.0
        issues = []

        experiences = content.get("experiences", [])

        # Check date consistency (5 points)
        date_formats = set()
        for exp in experiences:
            if exp.get("duration"):
                duration_str = exp["duration"]
                # Detect format patterns
                if re.search(r'\d{4}-\d{4}', duration_str):
                    date_formats.add("YYYY-YYYY")
                elif re.search(r'[A-Z][a-z]{2} \d{4}', duration_str):
                    date_formats.add("Mon YYYY")
                elif re.search(r'\d{1,2}/\d{4}', duration_str):
                    date_formats.add("MM/YYYY")

        if len(date_formats) <= 1:
            score += 5.0
        elif len(date_formats) == 2:
            score += 2.5
            issues.append(Issue(
                category="formatting",
                severity=IssueSeverity.MEDIUM,
                issue="Inconsistent date formats detected",
                location="Experience section",
                example=f"Mix of {' and '.join(date_formats)} formats"
            ))
        else:
            issues.append(Issue(
                category="formatting",
                severity=IssueSeverity.HIGH,
                issue="Multiple inconsistent date formats",
                location="Experience section",
                example=f"Found {len(date_formats)} different date formats"
            ))

        # Check section headers (5 points) - presence of key sections
        has_contact = bool(content.get("name") or content.get("email"))
        has_experience = bool(experiences)
        has_skills = bool(content.get("skills"))
        has_education = bool(content.get("education"))

        sections_present = sum([has_contact, has_experience, has_skills, has_education])
        score += (sections_present / 4) * 5.0

        if sections_present < 4:
            missing_sections = []
            if not has_contact: missing_sections.append("contact info")
            if not has_experience: missing_sections.append("experience")
            if not has_skills: missing_sections.append("skills")
            if not has_education: missing_sections.append("education")

            issues.append(Issue(
                category="formatting",
                severity=IssueSeverity.HIGH,
                issue=f"Missing standard sections: {', '.join(missing_sections)}",
                location="Overall structure"
            ))

        # Check structure (5 points) - bullet points in experience
        total_bullets = 0
        experiences_without_bullets = 0
        for exp in experiences:
            bullets = exp.get("responsibilities", [])
            if not bullets or len(bullets) == 0:
                experiences_without_bullets += 1
            else:
                total_bullets += len(bullets)

        if len(experiences) > 0:
            if experiences_without_bullets == 0:
                score += 5.0
            elif experiences_without_bullets <= len(experiences) / 2:
                score += 2.5
                issues.append(Issue(
                    category="formatting",
                    severity=IssueSeverity.MEDIUM,
                    issue="Some experience entries lack bullet points",
                    location="Experience section"
                ))
            else:
                issues.append(Issue(
                    category="formatting",
                    severity=IssueSeverity.HIGH,
                    issue="Most experience entries lack bullet points/descriptions",
                    location="Experience section"
                ))
        else:
            score += 2.5  # Partial credit if no experience

        # Check length (5 points) - estimate based on content volume
        word_count = self._estimate_word_count(content)
        if 400 <= word_count <= 800:  # Ideal for 1-2 pages
            score += 5.0
        elif 300 <= word_count < 400 or 800 < word_count <= 1000:
            score += 3.0
            issues.append(Issue(
                category="formatting",
                severity=IssueSeverity.LOW,
                issue=f"Resume length could be optimized (estimated {word_count} words)",
                location="Overall",
                example="Aim for 400-800 words for 1-2 pages"
            ))
        elif word_count < 300:
            score += 1.0
            issues.append(Issue(
                category="formatting",
                severity=IssueSeverity.HIGH,
                issue=f"Resume appears too short (estimated {word_count} words)",
                location="Overall"
            ))
        elif word_count > 1000:
            score += 2.0
            issues.append(Issue(
                category="formatting",
                severity=IssueSeverity.MEDIUM,
                issue=f"Resume may be too long (estimated {word_count} words)",
                location="Overall",
                example="Consider condensing to 1-2 pages"
            ))

        return score, issues

    def _score_content_quality(self, content: Dict) -> Tuple[float, List[Issue]]:
        """
        Score content quality (0-30 points)

        Checks:
        - Action verb usage (10 pts)
        - Quantifiable achievements (10 pts)
        - No personal pronouns (5 pts)
        - Strong accomplishments (5 pts)
        """
        score = 0.0
        issues = []

        experiences = content.get("experiences", [])
        all_bullets = []
        for exp in experiences:
            all_bullets.extend(exp.get("responsibilities", []))

        if not all_bullets:
            issues.append(Issue(
                category="content",
                severity=IssueSeverity.CRITICAL,
                issue="No bullet points found in experience section",
                location="Experience section"
            ))
            return 5.0, issues  # Minimal score for having experience at all

        # Check action verb usage (10 points)
        bullets_with_action_verbs = 0
        for bullet in all_bullets:
            first_word = bullet.strip().split()[0].lower().rstrip('.,!?')
            if first_word in self.ACTION_VERBS:
                bullets_with_action_verbs += 1

        action_verb_ratio = bullets_with_action_verbs / len(all_bullets)
        score += action_verb_ratio * 10.0

        if action_verb_ratio < 0.5:
            issues.append(Issue(
                category="content",
                severity=IssueSeverity.HIGH,
                issue=f"Only {int(action_verb_ratio*100)}% of bullet points start with strong action verbs",
                location="Experience section",
                example="Use verbs like: managed, coordinated, implemented, optimized"
            ))

        # Check quantifiable achievements (10 points)
        bullets_with_numbers = 0
        for bullet in all_bullets:
            # Look for numbers, percentages, dollar amounts
            if re.search(r'\d+[%$]?|\$\d+|[+-]\d+%', bullet):
                bullets_with_numbers += 1

        numbers_ratio = bullets_with_numbers / len(all_bullets)
        score += numbers_ratio * 10.0

        if numbers_ratio < 0.3:
            issues.append(Issue(
                category="content",
                severity=IssueSeverity.HIGH,
                issue=f"Only {int(numbers_ratio*100)}% of bullet points contain quantifiable achievements",
                location="Experience section",
                example="Add metrics like: 'Managed 15+ calendars', 'Reduced response time by 40%'"
            ))

        # Check for personal pronouns (5 points)
        text_content = " ".join(all_bullets).lower()
        pronouns = ['i ', 'my ', 'me ', 'we ', 'our ', 'us ']
        pronoun_count = sum(text_content.count(p) for p in pronouns)

        if pronoun_count == 0:
            score += 5.0
        elif pronoun_count <= 2:
            score += 3.0
            issues.append(Issue(
                category="content",
                severity=IssueSeverity.LOW,
                issue=f"Resume contains {pronoun_count} personal pronouns",
                location="Experience section",
                example="Avoid 'I', 'my', 'we' - use direct action statements"
            ))
        else:
            score += 1.0
            issues.append(Issue(
                category="content",
                severity=IssueSeverity.MEDIUM,
                issue=f"Resume contains {pronoun_count} personal pronouns",
                location="Experience section",
                example="Remove 'I', 'my', 'we' - start with action verbs directly"
            ))

        # Check accomplishment strength (5 points) - based on descriptive length
        avg_bullet_length = sum(len(b) for b in all_bullets) / len(all_bullets)

        if avg_bullet_length >= 80:  # Detailed accomplishments
            score += 5.0
        elif avg_bullet_length >= 50:
            score += 3.0
        elif avg_bullet_length >= 30:
            score += 2.0
            issues.append(Issue(
                category="content",
                severity=IssueSeverity.MEDIUM,
                issue="Bullet points are too brief - add more detail about impact",
                location="Experience section",
                example="Expand: 'Managed calendars' → 'Managed 10+ executive calendars, optimizing scheduling efficiency by 40%'"
            ))
        else:
            score += 1.0
            issues.append(Issue(
                category="content",
                severity=IssueSeverity.HIGH,
                issue="Bullet points are very brief and lack detail",
                location="Experience section"
            ))

        return score, issues

    def _score_ats_optimization(self, content: Dict) -> Tuple[float, List[Issue]]:
        """
        Score ATS optimization (0-25 points)

        Checks:
        - Standard section names (10 pts)
        - Keyword density for VA roles (10 pts)
        - Proper formatting (no tables/graphics) (5 pts)
        """
        score = 0.0
        issues = []

        # Standard sections (10 points) - already checked in formatting
        has_standard_sections = all([
            content.get("name") or content.get("email"),
            content.get("experiences"),
            content.get("skills"),
            content.get("education")
        ])
        score += 10.0 if has_standard_sections else 5.0

        # Keyword density (10 points)
        all_text = " ".join([
            content.get("summary", ""),
            " ".join([exp.get("role", "") + " " + " ".join(exp.get("responsibilities", []))
                     for exp in content.get("experiences", [])]),
            " ".join(content.get("skills", []))
        ]).lower()

        keyword_matches = 0
        for keyword in self.VA_KEYWORDS:
            if keyword.lower() in all_text:
                keyword_matches += 1

        keyword_ratio = keyword_matches / len(self.VA_KEYWORDS)
        score += keyword_ratio * 10.0

        if keyword_ratio < 0.15:  # Less than 15% of VA keywords
            issues.append(Issue(
                category="ats",
                severity=IssueSeverity.CRITICAL,
                issue="Very few VA-specific keywords detected",
                location="Overall content",
                example="Add keywords like: calendar management, administrative support, CRM, Asana, Google Workspace"
            ))
        elif keyword_ratio < 0.3:
            issues.append(Issue(
                category="ats",
                severity=IssueSeverity.HIGH,
                issue=f"Only {int(keyword_ratio*100)}% keyword coverage for VA roles",
                location="Overall content",
                example="Include more VA-specific terms and tools"
            ))

        # Proper formatting (5 points) - assume good unless we detect issues
        # Since we're parsing text, we can't directly check for tables/graphics
        # But we can check for proper structure
        score += 5.0

        return score, issues

    def _score_skills_section(self, content: Dict) -> Tuple[float, List[Issue]]:
        """
        Score skills section (0-15 points)

        Checks:
        - Presence of skills section (5 pts)
        - Number of skills (5 pts)
        - Relevance to VA role (5 pts)
        """
        score = 0.0
        issues = []

        skills = content.get("skills", [])

        # Presence (5 points)
        if skills and len(skills) > 0:
            score += 5.0
        else:
            issues.append(Issue(
                category="skills",
                severity=IssueSeverity.CRITICAL,
                issue="No skills section found",
                location="Skills section"
            ))
            return score, issues

        # Number of skills (5 points)
        if len(skills) >= 12:
            score += 5.0
        elif len(skills) >= 8:
            score += 3.5
        elif len(skills) >= 5:
            score += 2.0
            issues.append(Issue(
                category="skills",
                severity=IssueSeverity.MEDIUM,
                issue=f"Only {len(skills)} skills listed - aim for 10-15",
                location="Skills section",
                example="Add more specific tools and software you're proficient in"
            ))
        else:
            score += 1.0
            issues.append(Issue(
                category="skills",
                severity=IssueSeverity.HIGH,
                issue=f"Very few skills listed ({len(skills)}) - should have 10-15",
                location="Skills section"
            ))

        # Relevance (5 points) - check for VA-specific skills
        skills_lower = [s.lower() for s in skills]
        relevant_skills = 0
        for skill in skills_lower:
            for va_keyword in self.VA_KEYWORDS:
                if va_keyword in skill:
                    relevant_skills += 1
                    break

        relevance_ratio = relevant_skills / len(skills)
        score += relevance_ratio * 5.0

        if relevance_ratio < 0.3:
            issues.append(Issue(
                category="skills",
                severity=IssueSeverity.HIGH,
                issue=f"Only {int(relevance_ratio*100)}% of skills are VA-relevant",
                location="Skills section",
                example="Add VA-specific skills: Asana, Google Calendar, CRM tools, email management"
            ))

        return score, issues

    def _score_professional_summary(self, content: Dict) -> Tuple[float, List[Issue]]:
        """
        Score professional summary (0-10 points)

        Checks:
        - Presence of summary (3 pts)
        - Length and quality (4 pts)
        - Keywords present (3 pts)
        """
        score = 0.0
        issues = []

        summary = content.get("summary", "")

        # Presence (3 points)
        if not summary or len(summary.strip()) == 0:
            issues.append(Issue(
                category="summary",
                severity=IssueSeverity.HIGH,
                issue="No professional summary found",
                location="Summary section",
                example="Add a 2-3 sentence summary highlighting your VA experience and key strengths"
            ))
            return score, issues

        score += 3.0

        # Length and quality (4 points)
        word_count = len(summary.split())
        if 40 <= word_count <= 100:  # Ideal length
            score += 4.0
        elif 25 <= word_count < 40 or 100 < word_count <= 150:
            score += 2.5
            issues.append(Issue(
                category="summary",
                severity=IssueSeverity.LOW,
                issue=f"Summary length could be optimized ({word_count} words)",
                location="Summary section",
                example="Aim for 40-100 words (2-3 sentences)"
            ))
        elif word_count < 25:
            score += 1.0
            issues.append(Issue(
                category="summary",
                severity=IssueSeverity.MEDIUM,
                issue=f"Summary is too brief ({word_count} words)",
                location="Summary section"
            ))
        else:
            score += 2.0
            issues.append(Issue(
                category="summary",
                severity=IssueSeverity.MEDIUM,
                issue=f"Summary is too long ({word_count} words)",
                location="Summary section",
                example="Condense to 2-3 impactful sentences"
            ))

        # Keywords (3 points)
        summary_lower = summary.lower()
        keyword_count = sum(1 for kw in self.VA_KEYWORDS if kw in summary_lower)

        if keyword_count >= 3:
            score += 3.0
        elif keyword_count >= 2:
            score += 2.0
        elif keyword_count >= 1:
            score += 1.0
            issues.append(Issue(
                category="summary",
                severity=IssueSeverity.MEDIUM,
                issue="Summary lacks VA-specific keywords",
                location="Summary section",
                example="Include terms like: virtual assistant, administrative support, calendar management"
            ))
        else:
            issues.append(Issue(
                category="summary",
                severity=IssueSeverity.HIGH,
                issue="Summary has no VA-specific keywords",
                location="Summary section"
            ))

        return score, issues

    def _generate_suggestions(self, issues: List[Issue], content: Dict) -> List[Suggestion]:
        """Generate improvement suggestions based on issues"""
        suggestions = []

        # Group issues by severity
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]

        # Generate critical priority suggestions
        if any("quantifiable achievements" in i.issue.lower() for i in issues):
            suggestions.append(Suggestion(
                category="content",
                priority=SuggestionPriority.CRITICAL,
                suggestion="Add quantifiable metrics to demonstrate your impact",
                examples=[
                    "Managed 15+ executive calendars with 99% accuracy",
                    "Reduced email response time by 45% through automation",
                    "Coordinated travel for 20+ international trips annually"
                ],
                reasoning="Numbers make your achievements concrete and memorable to recruiters"
            ))

        if any("action verb" in i.issue.lower() for i in issues):
            suggestions.append(Suggestion(
                category="content",
                priority=SuggestionPriority.HIGH,
                suggestion="Start bullet points with strong action verbs",
                examples=[
                    "Coordinated", "Streamlined", "Optimized", "Managed", "Implemented"
                ],
                reasoning="Action verbs make your resume more dynamic and results-oriented"
            ))

        if any("keyword" in i.issue.lower() for i in issues):
            suggestions.append(Suggestion(
                category="ats",
                priority=SuggestionPriority.CRITICAL,
                suggestion="Optimize for ATS with VA-specific keywords",
                examples=[
                    "Administrative Support", "Calendar Management", "CRM (HubSpot, Salesforce)",
                    "Project Management Tools (Asana, Monday.com)", "Google Workspace", "Data Entry"
                ],
                reasoning="80% of resumes are filtered by ATS before human review"
            ))

        if any("skills" in i.category.lower() for i in issues):
            suggestions.append(Suggestion(
                category="skills",
                priority=SuggestionPriority.HIGH,
                suggestion="Expand your skills section with specific tools and platforms",
                examples=[
                    "Scheduling: Google Calendar, Calendly",
                    "Communication: Slack, Zoom, Microsoft Teams",
                    "Project Management: Asana, Trello, Monday.com",
                    "CRM: HubSpot, Salesforce, Pipedrive"
                ],
                reasoning="Specific tool proficiency helps you stand out and pass ATS filters"
            ))

        if any("summary" in i.category.lower() for i in critical_issues + high_issues):
            suggestions.append(Suggestion(
                category="summary",
                priority=SuggestionPriority.HIGH,
                suggestion="Craft a compelling professional summary that hooks recruiters",
                examples=[
                    "Detail-oriented Virtual Assistant with 5+ years supporting C-suite executives",
                    "Specialized in calendar optimization, reducing scheduling conflicts by 40%",
                    "Proficient in Google Workspace, Asana, and HubSpot"
                ],
                reasoning="Your summary is the first thing recruiters read - make it count"
            ))

        return suggestions

    def _extract_metadata(self, content: Dict) -> AnalysisMetadata:
        """Extract resume metadata"""
        # Estimate word count
        word_count = self._estimate_word_count(content)

        # Detect sections
        sections_found = []
        if content.get("name") or content.get("email"):
            sections_found.append("contact")
        if content.get("summary"):
            sections_found.append("summary")
        if content.get("experiences"):
            sections_found.append("experience")
        if content.get("education"):
            sections_found.append("education")
        if content.get("skills"):
            sections_found.append("skills")

        # Check for action verbs
        experiences = content.get("experiences", [])
        all_bullets = []
        for exp in experiences:
            all_bullets.extend(exp.get("responsibilities", []))

        has_action_verbs = any(
            bullet.strip().split()[0].lower().rstrip('.,!?') in self.ACTION_VERBS
            for bullet in all_bullets if bullet.strip()
        )

        # Check for quantifiable achievements
        has_quantifiable = any(
            re.search(r'\d+[%$]?|\$\d+|[+-]\d+%', bullet)
            for bullet in all_bullets
        )

        # Count VA keyword frequency
        all_text = " ".join([
            content.get("summary", ""),
            " ".join([exp.get("role", "") + " " + " ".join(exp.get("responsibilities", []))
                     for exp in experiences]),
            " ".join(content.get("skills", []))
        ]).lower()

        keyword_density = {}
        for keyword in self.VA_KEYWORDS:
            count = all_text.count(keyword.lower())
            if count > 0:
                keyword_density[keyword] = count

        return AnalysisMetadata(
            word_count=word_count,
            page_count=1 if word_count < 500 else 2,
            sections_found=sections_found,
            has_action_verbs=has_action_verbs,
            has_quantifiable_achievements=has_quantifiable,
            keyword_density=keyword_density
        )

    def _estimate_word_count(self, content: Dict) -> int:
        """Estimate total word count from resume content"""
        text_parts = [
            content.get("name", ""),
            content.get("email", ""),
            content.get("summary", ""),
            " ".join(content.get("skills", [])),
        ]

        for exp in content.get("experiences", []):
            text_parts.append(exp.get("role", ""))
            text_parts.append(exp.get("company", ""))
            text_parts.extend(exp.get("responsibilities", []))

        for edu in content.get("education", []):
            if isinstance(edu, dict):
                text_parts.append(edu.get("degree", ""))
                text_parts.append(edu.get("institution", ""))
            else:
                text_parts.append(str(edu))

        all_text = " ".join(text_parts)
        return len(all_text.split())
