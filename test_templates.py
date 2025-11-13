"""
Test script for resume templates
Tests all four templates with sample data and WeasyPrint
"""
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample resume data matching analyzer.py structure
SAMPLE_DATA = {
    "name": "Sarah Johnson",
    "title": "Senior Virtual Assistant",
    "email": "sarah.johnson@email.com",
    "phone": "+1 (555) 123-4567",
    "location": "Austin, TX",
    "linkedin": "linkedin.com/in/sarahjohnson",
    "website": "www.sarahjohnson.com",
    "summary": "Highly organized and detail-oriented Virtual Assistant with 5+ years of experience supporting C-level executives and managing complex administrative operations. Proven expertise in calendar management, travel coordination, email management, and project coordination. Skilled in CRM systems, project management tools, and Microsoft Office Suite. Known for exceptional communication skills and ability to handle multiple priorities with precision.",
    "experiences": [
        {
            "role": "Senior Virtual Assistant",
            "company": "Executive Support Services LLC",
            "location": "Remote",
            "start_date": "Jan 2021",
            "end_date": "Present",
            "responsibilities": [
                "Manage complex calendars for 3 C-level executives, coordinating 40+ meetings per week across multiple time zones",
                "Reduced scheduling conflicts by 95% through implementation of automated booking system",
                "Process and prioritize 200+ emails daily, maintaining 2-hour response time for urgent matters",
                "Coordinate international travel arrangements, resulting in 20% cost savings through strategic vendor negotiations",
                "Created and maintain comprehensive operations manual, reducing onboarding time for new team members by 50%"
            ]
        },
        {
            "role": "Virtual Assistant",
            "company": "Remote Pro Solutions",
            "location": "Remote",
            "start_date": "Mar 2019",
            "end_date": "Dec 2020",
            "responsibilities": [
                "Provided administrative support to small business owners and entrepreneurs",
                "Managed customer service inbox, maintaining 98% customer satisfaction rating",
                "Created social media content calendar and scheduled posts using Hootsuite and Buffer",
                "Processed invoices and expense reports using QuickBooks Online",
                "Coordinated virtual events and webinars for audiences of 50-200 participants"
            ]
        },
        {
            "role": "Administrative Coordinator",
            "company": "Tech Innovations Inc.",
            "location": "Austin, TX",
            "start_date": "Jun 2017",
            "end_date": "Feb 2019",
            "responsibilities": [
                "Supported operations team of 15 employees with scheduling, documentation, and reporting",
                "Maintained office supply inventory and vendor relationships",
                "Organized quarterly team building events and company meetings",
                "Assisted with onboarding of new employees and coordinated training schedules"
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
        },
        {
            "degree": "Certificate",
            "field": "Virtual Assistant Professional",
            "institution": "International Virtual Assistants Association",
            "graduation_date": "Dec 2019"
        }
    ],
    "skills": [
        "Calendar Management",
        "Email Management",
        "Travel Coordination",
        "CRM (Salesforce, HubSpot)",
        "Project Management (Asana, Trello, Monday.com)",
        "Microsoft Office Suite (Expert Level)",
        "Google Workspace",
        "Data Entry & Database Management",
        "Social Media Management",
        "Customer Service",
        "Bookkeeping (QuickBooks)",
        "Video Conferencing (Zoom, Teams, Meet)",
        "Document Preparation",
        "Research & Reporting",
        "Time Management",
        "Communication (Written & Verbal)"
    ],
    "certifications": [
        {
            "name": "Certified Administrative Professional (CAP)",
            "issuer": "International Association of Administrative Professionals",
            "date": "Jun 2020"
        },
        {
            "name": "Advanced Microsoft Office Specialist",
            "issuer": "Microsoft",
            "date": "Mar 2021"
        },
        {
            "name": "Project Management Fundamentals",
            "issuer": "LinkedIn Learning",
            "date": "Sep 2020"
        }
    ]
}

def test_template(template_name: str, data: dict, output_dir: Path):
    """
    Test a single template by rendering it and generating a PDF

    Args:
        template_name: Name of template (e.g., 'ats-optimized', 'professional')
        data: Resume data dictionary
        output_dir: Directory to save test PDFs
    """
    logger.info(f"Testing template: {template_name}")

    try:
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "app" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Load and render template
        template_file = f"{template_name}.html"
        template = env.get_template(template_file)
        html_content = template.render(content=data)

        logger.info(f"  ✓ Template rendered successfully ({len(html_content)} characters)")

        # Generate PDF
        output_file = output_dir / f"{template_name}_test.pdf"
        HTML(string=html_content).write_pdf(output_file)

        file_size = output_file.stat().st_size
        logger.info(f"  ✓ PDF generated successfully ({file_size:,} bytes)")
        logger.info(f"  ✓ Saved to: {output_file}")

        return True

    except Exception as e:
        logger.error(f"  ✗ Template test failed: {e}", exc_info=True)
        return False

def main():
    """Run tests for all templates"""
    logger.info("=" * 60)
    logger.info("Resume Template Testing")
    logger.info("=" * 60)

    # Create output directory for test PDFs
    output_dir = Path(__file__).parent / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    logger.info(f"Output directory: {output_dir}\n")

    # Templates to test
    templates = [
        "ats-optimized",
        "professional",
        "modern",
        "executive"
    ]

    results = {}

    # Test each template
    for template_name in templates:
        success = test_template(template_name, SAMPLE_DATA, output_dir)
        results[template_name] = success
        logger.info("")

    # Summary
    logger.info("=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)

    for template_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{template_name:20s} {status}")

    # Overall result
    all_passed = all(results.values())
    logger.info("")
    if all_passed:
        logger.info("✓ All templates passed!")
        logger.info(f"✓ Test PDFs saved to: {output_dir}")
        return 0
    else:
        failed_count = sum(1 for v in results.values() if not v)
        logger.error(f"✗ {failed_count}/{len(templates)} templates failed")
        return 1

if __name__ == "__main__":
    exit(main())
