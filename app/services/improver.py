"""
Resume Improver Service
Uses Claude AI to generate content improvements
"""
from typing import Dict, Any, List, Optional
import logging
import asyncio
from anthropic import AsyncAnthropic, APIError, RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.models.schemas import (
    ImproveResponse, Improvement, ImprovementType, ImproveRequest
)
from app.utils.config import get_settings

logger = logging.getLogger(__name__)


class ResumeImprover:
    """
    Generates AI-powered improvements using Claude with async/await
    """

    def __init__(self):
        """Initialize improver with async Claude API client"""
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)  # ASYNC client!
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
        self.timeout = 30.0  # 30 second timeout
        self.max_retries = 3
        logger.info("ResumeImprover initialized with async Claude API")

    async def improve(
        self,
        resume_improvement_id: str,
        content: Dict[str, Any],
        focus_areas: List[str]
    ) -> ImproveResponse:
        """
        Generate improvements for resume content

        Args:
            resume_improvement_id: Session ID
            content: Parsed resume content
            focus_areas: Areas to focus on (bullet_points, summary, keywords)

        Returns:
            ImproveResponse with list of improvements
        """
        logger.info(f"Generating improvements for: {resume_improvement_id}")
        logger.info(f"Focus areas: {focus_areas}")

        improvements = []

        # Process each focus area
        if "bullet_points" in focus_areas:
            improvements.extend(await self._improve_bullet_points(content))

        if "summary" in focus_areas:
            improvements.extend(await self._improve_summary(content))

        if "keywords" in focus_areas:
            improvements.extend(await self._add_keywords(content))

        # Calculate estimated score increase
        estimated_increase = len(improvements) * 1.5  # Simple heuristic

        return ImproveResponse(
            resume_improvement_id=resume_improvement_id,
            improvements=improvements,
            total_improvements=len(improvements),
            estimated_score_increase=min(estimated_increase, 25.0)  # Cap at 25 points
        )

    async def batch_improve(self, requests: List[ImproveRequest]) -> List[ImproveResponse]:
        """
        Batch process multiple improvement requests
        More efficient for multiple sections
        """
        results = []
        for request in requests:
            result = await self.improve(
                request.resume_improvement_id,
                request.content,
                request.focus_areas
            )
            results.append(result)
        return results

    async def _improve_bullet_points(self, content: Dict) -> List[Improvement]:
        """
        Use Claude to improve bullet points
        Adds action verbs, metrics, and impact
        """
        improvements = []

        # Extract experience bullet points
        experience = content.get("experience", [])

        for i, job in enumerate(experience):
            bullets = job.get("bullets", [])

            for j, bullet in enumerate(bullets):
                # Skip if already strong
                if self._is_strong_bullet(bullet):
                    continue

                # Generate improved version with Claude
                improved = await self._call_claude_for_bullet(bullet, job.get("title", ""))

                improvements.append(Improvement(
                    type=ImprovementType.BULLET_POINT,
                    original=bullet,
                    improved=improved,
                    section=f"experience[{i}].bullets[{j}]",
                    reasoning="Enhanced with action verb and quantifiable metrics",
                    confidence=0.9
                ))

        return improvements

    async def _improve_summary(self, content: Dict) -> List[Improvement]:
        """Use Claude to improve professional summary"""
        improvements = []
        summary = content.get("summary", "")

        if not summary or len(summary) < 50:
            # Generate new summary
            improved = await self._call_claude_for_summary(content)
            improvements.append(Improvement(
                type=ImprovementType.SUMMARY,
                original=summary,
                improved=improved,
                section="summary",
                reasoning="Created compelling value proposition with key achievements",
                confidence=0.95
            ))

        return improvements

    async def _add_keywords(self, content: Dict) -> List[Improvement]:
        """Suggest keyword additions for better ATS optimization"""
        improvements = []

        # VA-specific keywords to check
        important_keywords = [
            "calendar management",
            "email management",
            "administrative support",
            "project coordination",
            "client communication",
            "data entry",
            "CRM management",
            "scheduling",
            "travel coordination"
        ]

        # TODO: Analyze content and suggest missing keywords

        return improvements

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError, APITimeoutError)),
        reraise=True
    )
    async def _call_claude_for_bullet(self, bullet: str, job_title: str) -> str:
        """
        Call Claude API to improve a bullet point with retry logic

        Args:
            bullet: Original bullet point
            job_title: Job title for context

        Returns:
            Improved bullet point
        """
        prompt = f"""You are an expert resume writer specializing in Virtual Assistant roles.

Improve this bullet point from a {job_title} position:
"{bullet}"

Requirements:
- Start with a strong action verb
- Add specific metrics or quantifiable achievements where logical
- Keep it concise (under 150 characters)
- Make it impactful and results-oriented
- Focus on VA-relevant skills (calendar management, email, admin, communication)

Return ONLY the improved bullet point, nothing else."""

        try:
            # PROPERLY ASYNC call with await!
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0.7,
                timeout=self.timeout,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            improved = message.content[0].text.strip()
            logger.info(f"Claude improved bullet: {bullet[:50]}... -> {improved[:50]}...")
            return improved

        except RateLimitError as e:
            logger.warning(f"Claude rate limit hit: {e}")
            raise  # Retry will handle this
        except APITimeoutError as e:
            logger.warning(f"Claude timeout: {e}")
            raise  # Retry will handle this
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise  # Retry will handle this
        except Exception as e:
            logger.error(f"Unexpected Claude error: {e}", exc_info=True)
            # For unexpected errors, return original instead of failing completely
            return bullet

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError, APITimeoutError)),
        reraise=True
    )
    async def _call_claude_for_summary(self, content: Dict) -> str:
        """
        Call Claude API to generate professional summary with retry logic

        Args:
            content: Full resume content for context

        Returns:
            Improved professional summary
        """
        # Extract key info from content
        experience = content.get("experience", [])
        skills = content.get("skills", [])
        title = content.get("title", "Virtual Assistant")

        prompt = f"""You are an expert resume writer specializing in Virtual Assistant roles.

Create a compelling professional summary (2-3 sentences, max 250 characters) for a {title} with:
- Experience: {len(experience)} positions
- Key skills: {', '.join(skills[:5])}

Requirements:
- Start with years of experience or standout qualification
- Highlight 2-3 key strengths or achievements
- Include VA-relevant skills
- End with value proposition
- Professional but engaging tone

Return ONLY the summary, nothing else."""

        try:
            # PROPERLY ASYNC call with await!
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.8,
                timeout=self.timeout,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary = message.content[0].text.strip()
            logger.info(f"Claude generated summary: {summary[:100]}...")
            return summary

        except RateLimitError as e:
            logger.warning(f"Claude rate limit hit: {e}")
            raise  # Retry will handle this
        except APITimeoutError as e:
            logger.warning(f"Claude timeout: {e}")
            raise  # Retry will handle this
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise  # Retry will handle this
        except Exception as e:
            logger.error(f"Unexpected Claude error: {e}", exc_info=True)
            # For unexpected errors, return fallback
            return "Experienced Virtual Assistant with proven track record in administrative support and client management."

    def _is_strong_bullet(self, bullet: str) -> bool:
        """
        Check if bullet point is already strong
        Returns True if no improvement needed
        """
        # Check for action verbs
        action_verbs = ["managed", "coordinated", "led", "developed", "implemented", "optimized"]
        has_action_verb = any(bullet.lower().startswith(verb) for verb in action_verbs)

        # Check for numbers/metrics
        has_metrics = any(char.isdigit() for char in bullet)

        # Check length
        good_length = 50 < len(bullet) < 200

        return has_action_verb and has_metrics and good_length
