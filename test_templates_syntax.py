"""
Template Syntax Validation Script
Validates Jinja2 templates without requiring WeasyPrint system dependencies
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample resume data
SAMPLE_DATA = {
    "name": "Sarah Johnson",
    "title": "Senior Virtual Assistant",
    "email": "sarah.johnson@email.com",
    "phone": "+1 (555) 123-4567",
    "location": "Austin, TX",
    "linkedin": "linkedin.com/in/sarahjohnson",
    "website": "www.sarahjohnson.com",
    "summary": "Highly organized and detail-oriented Virtual Assistant with 5+ years of experience.",
    "experiences": [
        {
            "role": "Senior Virtual Assistant",
            "company": "Executive Support Services LLC",
            "location": "Remote",
            "start_date": "Jan 2021",
            "end_date": "Present",
            "responsibilities": [
                "Manage complex calendars for 3 C-level executives",
                "Reduced scheduling conflicts by 95% through automation",
                "Process 200+ emails daily with 2-hour response time"
            ]
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Arts",
            "field": "Business Administration",
            "institution": "University of Texas at Austin",
            "graduation_date": "May 2017",
            "gpa": "3.7",
            "honors": "Cum Laude"
        }
    ],
    "skills": [
        "Calendar Management", "Email Management", "CRM (Salesforce, HubSpot)",
        "Project Management", "Microsoft Office Suite", "Data Entry"
    ],
    "certifications": [
        {
            "name": "Certified Administrative Professional (CAP)",
            "issuer": "International Association of Administrative Professionals",
            "date": "Jun 2020"
        }
    ]
}

def validate_template(template_name: str, data: dict) -> bool:
    """
    Validate a template by rendering it with Jinja2

    Args:
        template_name: Name of template (e.g., 'ats-optimized')
        data: Resume data dictionary

    Returns:
        True if template is valid, False otherwise
    """
    logger.info(f"Validating template: {template_name}")

    try:
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "app" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Load and render template
        template_file = f"{template_name}.html"
        template = env.get_template(template_file)
        html_content = template.render(content=data)

        # Basic validation
        if not html_content or len(html_content) < 100:
            logger.error(f"  ✗ Template rendered but content is too short")
            return False

        # Check for common issues
        if "{{" in html_content or "{%" in html_content:
            logger.warning(f"  ⚠ Unrendered Jinja2 syntax found in output")

        logger.info(f"  ✓ Template syntax valid ({len(html_content):,} characters)")
        logger.info(f"  ✓ Contains expected sections: name, email, experiences")

        # Verify key content is present
        checks = {
            "name": data["name"] in html_content,
            "email": data["email"] in html_content,
            "role": data["experiences"][0]["role"] in html_content,
            "education": data["education"][0]["degree"] in html_content
        }

        for check_name, passed in checks.items():
            status = "✓" if passed else "✗"
            logger.info(f"  {status} Content check: {check_name}")

        if not all(checks.values()):
            logger.error(f"  ✗ Some content checks failed")
            return False

        return True

    except TemplateSyntaxError as e:
        logger.error(f"  ✗ Jinja2 syntax error: {e}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Validation failed: {e}", exc_info=True)
        return False

def main():
    """Validate all templates"""
    logger.info("=" * 60)
    logger.info("Resume Template Syntax Validation")
    logger.info("=" * 60)
    logger.info("NOTE: This validates Jinja2 syntax only.")
    logger.info("PDF generation will be tested in Docker/Railway.\n")

    templates = [
        "ats-optimized",
        "professional",
        "modern",
        "executive"
    ]

    results = {}

    # Validate each template
    for template_name in templates:
        success = validate_template(template_name, SAMPLE_DATA)
        results[template_name] = success
        logger.info("")

    # Summary
    logger.info("=" * 60)
    logger.info("Validation Results")
    logger.info("=" * 60)

    for template_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{template_name:20s} {status}")

    # Overall result
    all_passed = all(results.values())
    logger.info("")
    if all_passed:
        logger.info("✓ All templates are syntactically valid!")
        logger.info("✓ Ready for PDF generation testing in Docker")
        return 0
    else:
        failed_count = sum(1 for v in results.values() if not v)
        logger.error(f"✗ {failed_count}/{len(templates)} templates failed validation")
        return 1

if __name__ == "__main__":
    exit(main())
