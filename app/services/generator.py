"""
Resume Generator Service
Generates PDF resumes from HTML templates using WeasyPrint
"""
from typing import Dict, Any
import logging
from datetime import datetime
import uuid
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from supabase import create_client, Client
from app.models.schemas import GenerateResponse, ResumeTemplate
from app.utils.config import get_settings

logger = logging.getLogger(__name__)


class ResumeGenerator:
    """
    Generates PDF resumes from HTML templates with secure storage
    """

    def __init__(self):
        """Initialize generator with Jinja2 template environment and Supabase client"""
        # Setup Jinja2 template loader
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Initialize Supabase client for storage
        settings = get_settings()
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY  # Use service role for storage operations
        )

        logger.info(f"ResumeGenerator initialized with templates from: {template_dir}")

    async def generate(
        self,
        resume_improvement_id: str,
        template: ResumeTemplate,
        content: Dict[str, Any],
        user_id: str
    ) -> GenerateResponse:
        """
        Generate PDF resume from template

        Args:
            resume_improvement_id: Session ID
            template: Template to use
            content: Resume content
            user_id: User ID for storage path

        Returns:
            GenerateResponse with download URL and file info
        """
        logger.info(f"Generating PDF with template: {template}")

        try:
            # Load and render template
            html_content = self._render_template(template, content)

            # Generate PDF
            pdf_bytes = self._html_to_pdf(html_content)

            # Upload to storage
            file_url, file_name = await self._upload_to_storage(
                pdf_bytes,
                user_id,
                resume_improvement_id,
                template
            )

            logger.info(f"Generated PDF: {file_name} ({len(pdf_bytes)} bytes)")

            return GenerateResponse(
                resume_improvement_id=resume_improvement_id,
                template=template,
                file_url=file_url,
                file_name=file_name,
                file_size=len(pdf_bytes),
                generated_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            raise

    def _render_template(self, template: ResumeTemplate, content: Dict[str, Any]) -> str:
        """
        Render HTML template with content

        Args:
            template: Template to use
            content: Resume data

        Returns:
            Rendered HTML string
        """
        template_file = f"{template.value}.html"

        try:
            jinja_template = self.env.get_template(template_file)
            html = jinja_template.render(
                content=content,
                generated_date=datetime.now().strftime("%B %Y")
            )
            return html

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise

    def _html_to_pdf(self, html_content: str) -> bytes:
        """
        Convert HTML to PDF using WeasyPrint

        Args:
            html_content: Rendered HTML

        Returns:
            PDF bytes
        """
        try:
            pdf = HTML(string=html_content).write_pdf()
            return pdf

        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            raise

    async def _upload_to_storage(
        self,
        pdf_bytes: bytes,
        user_id: str,
        resume_improvement_id: str,
        template: ResumeTemplate
    ) -> tuple[str, str]:
        """
        Upload PDF to Supabase storage and generate signed URL

        Args:
            pdf_bytes: PDF file bytes
            user_id: User ID
            resume_improvement_id: Session ID
            template: Template used

        Returns:
            Tuple of (signed_url, file_name)
        """
        try:
            # Generate unique file name
            file_name = f"resume_improved_{template.value}_{resume_improvement_id[:8]}.pdf"
            file_path = f"{user_id}/{file_name}"

            logger.info(f"Uploading PDF to Supabase storage: {file_path}")

            # Upload to private bucket
            upload_response = self.supabase.storage.from_("resume-improvements").upload(
                path=file_path,
                file=pdf_bytes,
                file_options={
                    "content-type": "application/pdf",
                    "upsert": "true"  # Allow re-upload if exists
                }
            )

            if hasattr(upload_response, 'error') and upload_response.error:
                logger.error(f"Upload error: {upload_response.error}")
                raise Exception(f"Storage upload failed: {upload_response.error}")

            logger.info(f"Upload successful: {file_path}")

            # Generate signed URL (expires in 1 hour)
            signed_url_response = self.supabase.storage.from_("resume-improvements").create_signed_url(
                path=file_path,
                expires_in=3600  # 1 hour expiration
            )

            if hasattr(signed_url_response, 'error') and signed_url_response.error:
                logger.error(f"Signed URL error: {signed_url_response.error}")
                raise Exception(f"Failed to generate signed URL: {signed_url_response.error}")

            signed_url = signed_url_response.get('signedURL')
            if not signed_url:
                raise Exception("No signed URL returned from Supabase")

            logger.info(f"Generated signed URL (expires in 1 hour): {signed_url[:50]}...")
            return signed_url, file_name

        except Exception as e:
            logger.error(f"Storage operation failed: {e}", exc_info=True)
            raise Exception(f"Failed to upload and generate secure download URL: {str(e)}")

    async def get_template_preview(self, template: str) -> str:
        """
        Get preview/thumbnail URL for a template

        Args:
            template: Template ID

        Returns:
            Preview URL
        """
        return f"/static/templates/{template}-preview.png"
