"""
app/ingestion/portfolio_loader.py
───────────────────────────────────
Loads portfolio.json → converts each section to rich text chunks → returns chunk list.
"""

import json
import logging
from pathlib import Path
from app.ingestion.chunker import SmartChunker

logger = logging.getLogger(__name__)


class PortfolioLoader:
    def __init__(self):
        self.chunker = SmartChunker()

    def load(self, json_path: str) -> dict:
        """Load and return raw portfolio dict."""
        with open(json_path, "r") as f:
            return json.load(f)

    def build_chunks(self, portfolio: dict) -> list[dict]:
        """
        Convert portfolio JSON into richly-formatted text chunks.
        Each section gets its own source label for metadata.
        """
        chunks = []

        # ── Identity / About Me ────────────────────────────────────────
        identity = portfolio.get("identity", {})
        identity_text = f"""
About Me:
Name: {identity.get('full_name', identity.get('name', ''))}
Role: {identity.get('tagline', '')}
Summary: {identity.get('summary', '')}
Location: {identity.get('location', '')}
Years of Experience: {identity.get('years_of_experience', '')}
LinkedIn: {identity.get('linkedin', '')}
GitHub: {identity.get('github', '')}
Portfolio: {identity.get('portfolio_url', '')}
""".strip()
        chunks.extend(self.chunker.chunk_prose(identity_text, "portfolio/identity"))

        # ── Skills ─────────────────────────────────────────────────────
        skills = portfolio.get("skills", {})
        skills_text = "Technical Skills:\n"
        for category, skill_list in skills.items():
            skills_text += f"\n{category.replace('_', ' ').title()}: {', '.join(skill_list)}"
        chunks.extend(self.chunker.chunk_prose(skills_text, "portfolio/skills"))

        # ── Strengths ──────────────────────────────────────────────────
        strengths = portfolio.get("strengths", [])
        if strengths:
            strengths_text = "Key Strengths:\n" + "\n".join(f"- {s}" for s in strengths)
            chunks.extend(self.chunker.chunk_prose(strengths_text, "portfolio/strengths"))

        # ── Projects ───────────────────────────────────────────────────
        for project in portfolio.get("projects", []):
            project_text = f"""
Project: {project['name']}
Description: {project['description']}
Tech Stack: {', '.join(project.get('tech_stack', []))}
Architecture: {project.get('architecture', '')}
Challenges & Solutions: {project.get('challenges', '')}
Scalability: {project.get('scalability', '')}
Future Plans: {project.get('future', '')}
Demo: {project.get('demo_url', 'Not deployed yet')}
GitHub: {project.get('github_url', '')}
""".strip()
            chunks.extend(
                self.chunker.chunk_prose(project_text, f"portfolio/projects/{project['name']}")
            )

        # ── Certifications ─────────────────────────────────────────────
        for cert in portfolio.get("certifications", []):
            cert_text = f"""
Certification: {cert['name']}
Issued By: {cert['issuer']}
Year: {cert.get('year', '')}
Credential ID: {cert.get('credential_id', '')}
Skills Gained: {cert.get('skills_gained', '')}
""".strip()
            chunks.extend(self.chunker.chunk_prose(cert_text, f"portfolio/certifications/{cert['name']}"))

        # ── Achievements ───────────────────────────────────────────────
        achievements = portfolio.get("achievements", [])
        if achievements:
            ach_text = "Achievements:\n"
            for a in achievements:
                ach_text += f"\n[{a.get('year', '')}] {a['title']} — {a['description']} (Org: {a.get('organization', '')})"
            chunks.extend(self.chunker.chunk_prose(ach_text, "portfolio/achievements"))

        # ── Experience ─────────────────────────────────────────────────
        for exp in portfolio.get("experience", []):
            exp_text = f"""
Work Experience: {exp['title']} at {exp['company']}
Duration: {exp['duration']}
Description: {exp['description']}
Technologies Used: {', '.join(exp.get('tech', []))}
""".strip()
            chunks.extend(self.chunker.chunk_prose(exp_text, f"portfolio/experience/{exp['company']}"))

        # ── Education ──────────────────────────────────────────────────
        edu = portfolio.get("education", {})
        if edu:
            edu_text = f"""
Education: {edu.get('degree', '')}
Institution: {edu.get('institution', '')}
Year: {edu.get('year', '')}
CGPA: {edu.get('cgpa', '')}
Relevant Courses: {', '.join(edu.get('relevant_courses', []))}
""".strip()
            chunks.extend(self.chunker.chunk_prose(edu_text, "portfolio/education"))

        # ── Interests ──────────────────────────────────────────────────
        interests = portfolio.get("interests", {})
        if interests:
            int_text = "Interests & Career Direction:\n"
            for k, v in interests.items():
                int_text += f"\n{k.title()}: {', '.join(v) if isinstance(v, list) else v}"
            chunks.extend(self.chunker.chunk_prose(int_text, "portfolio/interests"))

        # ── Personality ────────────────────────────────────────────────
        traits = portfolio.get("personality_traits", [])
        if traits:
            traits_text = "Personality & Work Style:\n" + "\n".join(f"- {t}" for t in traits)
            chunks.extend(self.chunker.chunk_prose(traits_text, "portfolio/personality"))

        logger.info(f"Portfolio loaded: {len(chunks)} chunks generated")
        return chunks
