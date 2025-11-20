"""
Internal Resume Parser using PyMuPDF

Eliminates dependency on external parsing services.
Extracts text and structure from PDF resumes.
"""
import re
import fitz  # PyMuPDF
import httpx
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Internal resume parser using PyMuPDF for text extraction
    """

    async def parse_resume(
        self,
        resume_url: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse a resume from URL and extract structured data

        Args:
            resume_url: Public URL to resume PDF
            user_id: Optional user ID for tracking

        Returns:
            Structured resume data dict
        """
        try:
            logger.info(f"Parsing resume from: {resume_url}")

            # Download PDF
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(resume_url)
                response.raise_for_status()
                pdf_bytes = response.content

            # Extract text from PDF
            full_text = self._extract_text_from_pdf(pdf_bytes)
            logger.info(f"Extracted {len(full_text)} characters of text")

            # Parse structure
            parsed_data = self._parse_resume_text(full_text)

            return parsed_data

        except Exception as e:
            logger.error(f"Failed to parse resume: {str(e)}", exc_info=True)
            raise Exception(f"Failed to parse resume: {str(e)}")

    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF

        Args:
            pdf_bytes: PDF file bytes

        Returns:
            Extracted text string
        """
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            # Extract text from all pages
            full_text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                full_text += page.get_text() + "\n"

            doc.close()

            return full_text.strip()

        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise

    def _parse_resume_text(self, text: str) -> Dict[str, Any]:
        """
        Parse resume text into structured data

        Args:
            text: Raw resume text

        Returns:
            Structured resume data
        """
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]

        # Extract contact information
        name = self._extract_name(lines)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        location = self._extract_location(text)
        linkedin = self._extract_linkedin(text)

        # Extract sections
        summary = self._extract_section(text, ['summary', 'profile', 'objective', 'about'])
        experiences = self._extract_experiences(text)
        education = self._extract_education(text)
        skills = self._extract_skills(text)

        return {
            "name": name or "Resume Applicant",
            "email": email or "",
            "phone": phone or "",
            "location": location or "",
            "linkedin": linkedin or "",
            "summary": summary or "",
            "experiences": experiences,
            "education": education,
            "skills": skills,
            "metadata": {
                "source": "internal-pymupdf-parser",
                "version": "1.0.0",
                "text_length": len(text)
            }
        }

    def _extract_name(self, lines: List[str]) -> str:
        """Extract name (typically first line)"""
        if not lines:
            return ""

        # First line is usually the name
        first_line = lines[0]

        # If first line looks like a name (2-4 words, mostly caps or title case)
        words = first_line.split()
        if 2 <= len(words) <= 4 and not any(char in first_line for char in '@|•'):
            return first_line

        return ""

    def _extract_email(self, text: str) -> str:
        """Extract email address"""
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_regex, text)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        phone_regex = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(phone_regex, text)
        return match.group(0) if match else ""

    def _extract_location(self, text: str) -> str:
        """Extract location (city, state)"""
        # Look for City, ST or City, State patterns
        location_regex = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})|([A-Z][a-z]+,\s*[A-Z][a-z]+)'
        match = re.search(location_regex, text)
        return match.group(0) if match else ""

    def _extract_linkedin(self, text: str) -> str:
        """Extract LinkedIn URL"""
        linkedin_regex = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
        match = re.search(linkedin_regex, text, re.IGNORECASE)
        return match.group(0) if match else ""

    def _extract_section(self, text: str, headers: List[str]) -> str:
        """
        Extract a section by looking for common header patterns

        Args:
            text: Full resume text
            headers: List of possible header names

        Returns:
            Section text
        """
        for header in headers:
            # Look for header followed by content until next section
            pattern = rf'{header}[:\s]+(.+?)(?=\n\n|\n[A-Z][A-Z\s]+:|\n(EXPERIENCE|EDUCATION|SKILLS|CERTIFICATIONS)|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Limit to reasonable length
                return content[:500] if len(content) > 500 else content

        return ""

    def _extract_experiences(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract work experience entries

        Returns:
            List of experience dicts
        """
        experiences = []

        # Find EXPERIENCE section
        exp_pattern = r'(EXPERIENCE|WORK HISTORY|EMPLOYMENT|PROFESSIONAL EXPERIENCE)[:\s]*(.+?)(?=(EDUCATION|SKILLS|CERTIFICATIONS|PROJECTS|$))'
        exp_match = re.search(exp_pattern, text, re.IGNORECASE | re.DOTALL)

        if not exp_match:
            return []

        exp_section = exp_match.group(2)

        # Split into individual entries (usually separated by blank lines or date patterns)
        entries = re.split(r'\n\s*\n', exp_section)

        for entry in entries[:5]:  # Limit to 5 experiences
            if len(entry.strip()) < 30:
                continue

            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if len(lines) < 2:
                continue

            # Parse entry structure
            # Typically: Title, Company/Location, Date, Bullets
            role = lines[0] if lines else "Position"
            company_line = lines[1] if len(lines) > 1 else "Company"

            # Extract dates if present
            date_pattern = r'(\d{4}\s*[-–]\s*(?:\d{4}|Present))|([A-Za-z]+\s+\d{4}\s*[-–]\s*(?:[A-Za-z]+\s+\d{4}|Present))'
            date_match = re.search(date_pattern, entry)
            duration = date_match.group(0) if date_match else "Date range not specified"

            # Extract bullet points
            bullets = []
            for line in lines[2:]:
                # Look for bullet point indicators or action verb starts
                if any(line.startswith(indicator) for indicator in ['•', '-', '–', '◦', '*']):
                    bullets.append(line.lstrip('•-–◦* ').strip())
                elif len(line) > 20 and any(verb in line.lower()[:30] for verb in [
                    'led', 'managed', 'developed', 'created', 'improved', 'increased',
                    'reduced', 'achieved', 'delivered', 'implemented', 'designed'
                ]):
                    bullets.append(line)

            if not bullets:
                bullets = ["Responsibilities not detailed in resume"]

            experiences.append({
                "role": role,
                "company": company_line,
                "duration": duration,
                "responsibilities": bullets[:8]  # Limit bullets
            })

        return experiences

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract education entries

        Returns:
            List of education dicts
        """
        education = []

        # Find EDUCATION section
        edu_pattern = r'(EDUCATION|ACADEMIC|QUALIFICATION)[:\s]*(.+?)(?=(EXPERIENCE|SKILLS|CERTIFICATIONS|PROJECTS|$))'
        edu_match = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)

        if not edu_match:
            return []

        edu_section = edu_match.group(2)

        # Split into entries
        entries = re.split(r'\n\s*\n', edu_section)

        for entry in entries[:3]:  # Limit to 3 education entries
            if len(entry.strip()) < 15:
                continue

            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if not lines:
                continue

            # Parse degree and institution
            degree = lines[0] if lines else "Degree"
            institution = lines[1] if len(lines) > 1 else "Institution"

            # Extract graduation date
            date_pattern = r'(\d{4})|([A-Za-z]+\s+\d{4})'
            date_match = re.search(date_pattern, entry)
            grad_date = date_match.group(0) if date_match else ""

            # Look for GPA
            gpa_pattern = r'GPA[:\s]*([0-9.]+)'
            gpa_match = re.search(gpa_pattern, entry, re.IGNORECASE)
            gpa = gpa_match.group(1) if gpa_match else ""

            education.append({
                "degree": degree,
                "institution": institution,
                "graduation_date": grad_date,
                "gpa": gpa
            })

        return education if education else [{"degree": "Education section not fully parsed", "institution": ""}]

    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract skills list

        Returns:
            List of skill strings
        """
        # Find SKILLS section
        skills_pattern = r'(SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES)[:\s]*(.+?)(?=(EXPERIENCE|EDUCATION|CERTIFICATIONS|PROJECTS|$))'
        skills_match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)

        if not skills_match:
            return ["Skills section not found"]

        skills_text = skills_match.group(2)

        # Split by common delimiters
        skills = re.split(r'[,•\-\n|]', skills_text)
        skills = [s.strip() for s in skills if s.strip()]

        # Filter out noise
        skills = [s for s in skills if 3 <= len(s) <= 100]

        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)

        return unique_skills[:25]  # Limit to 25 skills
