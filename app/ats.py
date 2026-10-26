import re, math
from io import BytesIO
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from llama_cpp import Llama

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import mm

import pymupdf
from .skillgap import ROLE_SKILLS, normalize_text

# Common ATS Sections
CRITICAL_SECTIONS = {
    'contact': ['phone', 'email', 'linkedin', 'github', 'address', 'contact'],
    'education': ['education', 'academic', 'degree', 'bachelor', 'master', 'university', 'college'],
    'skills': ['skills', 'technical skills', 'core competencies', 'technologies', 'tools'],
    'projects': ['projects', 'academic projects', 'portfolio', 'personal projects'],
    'experience': ['experience', 'work experience', 'internship', 'employment'],
    'certifications': ['certifications', 'certificates', 'credentials', 'licenses']
}

@lru_cache(maxsize=1)
def get_minilm_model():
    model_path = Path(settings.MINILM_MODEL_PATH)

    if not model_path.is_file():
        raise FileNotFoundError(
            f"GGUF Model not found: {model_path}"
        )

    return Llama(
        model_path=str(model_path),
        embedding=True, n_ctx=512, verbose=False
    )   

# ---- Cosine Similarity ----
def cosine_similarity(vector_a,vector_b):
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b)) 
    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)  

def get_embedding(model,text):
    text = normalize_text(text or "")

    if not text:
        return None

    # ---- Preferred API ---- 
    if hasattr(model,"embed"):
        embedding = model.embed(text)
        if embedding and isinstance(embedding[0],list):
            return embedding[0]
        return embedding

    result = model.create_embedding(text)
    return result["data"][0]["embedding"] 

def resume_chunks(resume_text):
    text = str(resume_text or "").strip()

    if not text:
        return []

    chunks = [
        normalize_text(chunk)
        for chunk in re.split(r"[\n\r.!?;]+", text)
        if normalize_text(chunk)
    ]  
    return chunks[:300] 

# ---- Skill Similarity ----
def semantic_skill_match(skill,resume_chunks,model,threshold):
    skill_text = normalize_text(skill)

    if not skill_text or not resume_chunks:
        return 0.0, False

    skill_embedding = get_embedding(model, skill_text)

    if not skill_embedding:
        return 0.0, False

    best_similarity = 0.0   

    for chunk in resume_chunks:
        chunk_embedding = get_embedding(model,chunk)
        
        if not chunk_embedding:
            continue
        
        similarity = cosine_similarity(skill_embedding,chunk_embedding)
        best_similarity = max(best_similarity, similarity)
        
        if similarity >= threshold:
            return similarity, True

    return best_similarity, best_similarity >= threshold

# ---- Skill Match ----
def get_semantic_skill_matches(skills,resume_text):
    if not skills or not resume_text:
        return [],{}

    model = get_minilm_model()
    threshold = float(getattr(settings,"ATS_SEMANTIC_THRESHOLD",0.55)) 
    chunks = resume_chunks(resume_text)
    semantic_matches = []
    semantic_scores = {}

    for skill in skills:
        similarity, matched = semantic_skill_match(
            skill,chunks,model,threshold
        )
        semantic_scores[skill] = round(similarity*100)
        if matched:
            semantic_matches.append(skill)

    return semantic_matches, semantic_scores        

# ---- Resume ATS Analysis ----
def analyze_resume_for_ats(resume_text, target_role="python", job_description="", profile_skills=None):
    norm_text = normalize_text(resume_text or "")
    if profile_skills:
        norm_text += " " + " ".join(
            [normalize_text(s) for s in profile_skills]
        )

    target_role = (target_role or "python").strip().lower()

    role_skill_dict = ROLE_SKILLS.get(
        target_role,
        ROLE_SKILLS.get('python', {})
    )
    target_skills = list(role_skill_dict.keys())

    # If job description provided, extract additional keywords
    additional_reqs = []
    if job_description:
        jd_norm = normalize_text(job_description)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', jd_norm)
        for w in words:
            if w in [s.lower() for s in target_skills]:
                continue
            if len(w) > 3 and w not in ['with', 'from', 'have', 'experience', 'required', 'candidate', 'responsibilities']:
                additional_reqs.append(w)
        for skill in additional_reqs[:5]:
            if skill not in target_skills:
                target_skills.append(skill)

    # Check Matched vs Missing Skills
    exact_matched_skills = []
    unmatched_skills = []

    for skill in target_skills:
        skill_clean = normalize_text(skill)
        pattern = r"\b" + re.escape(skill_clean)+r"\b"

        if re.search(pattern,norm_text):
            exact_matched_skills.append(skill)
        else:
            unmatched_skills.append(skill)   

    semantic_matched_skills, semantic_scores = (
        get_semantic_skill_matches(
            unmatched_skills,resume_text
        ) 
    )
    matched_skills = (
        exact_matched_skills + semantic_matched_skills
    )  
    missing_skills = [
        skill
        for skill in unmatched_skills
        if skill not in semantic_matched_skills
]       

    # Section Detection
    detected_sections = {}
    detected_section_names = []
    missing_sections = []

    for sec_name, sec_keywords in CRITICAL_SECTIONS.items():
        found = any(
            re.search(r"\b" + re.escape(kw) + r"\b", norm_text) 
            for kw in sec_keywords
        )
        detected_sections[sec_name] = found
        if found:
            detected_section_names.append(sec_name.capitalize())
        else:    
            missing_sections.append(sec_name.capitalize())

    section_score = round((sum(1 for v in detected_sections.values() if v) / len(CRITICAL_SECTIONS)) * 100)
    keyword_score = round((len(matched_skills) / max(len(target_skills), 1)) * 100)

    # Content length & formatting readability
    words_count = len(norm_text.split())
    if 150 <= words_count <= 800:
        length_score = 95
    elif words_count < 150:
        length_score = max(20, round(words_count / 150 * 80))
    else:
        length_score = max(60, 100 - round((words_count - 800) / 20))

    # Overall ATS Suitability Score (Weighted: 50% Keywords, 30% Sections, 20% Readability)
    ats_score = round((keyword_score * 0.50) + (section_score * 0.30) + (length_score * 0.20))

    # Optimization Suggestions
    suggestions = []
    if missing_skills:
        suggestions.append(f"Add key technical keywords: {', '.join(missing_skills[:5])} to pass ATS filter algorithms.")
    if 'Projects' in missing_sections:
        suggestions.append("Add a dedicated 'Projects' section showcasing real-world implementations.")
    if 'Certifications' in missing_sections:
        suggestions.append("Include industry certifications or verified skill credentials to enhance authority.")
    if words_count < 200:
        suggestions.append("Expand on your technical achievements and duties to increase keyword density.")
    else:
        suggestions.append("Ensure your bullet points quantify achievements (e.g. 'Improved speed by 25%').")

    if not suggestions:
        suggestions.append("Resume structure and keyword density are well-optimized for ATS systems!")

    return {
        'score': ats_score, 'keyword_score': keyword_score,
        'section_score': section_score, 'length_score': length_score,
        'word_count': words_count, 'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'exact_matched_skills': exact_matched_skills,
        'semantic_matched_skills': semantic_matched_skills,
        'semantic_scores': semantic_scores,
        'detected_sections': detected_sections,
        'detected_section_names':detected_section_names,
        'missing_sections': missing_sections,
        'suggestions': suggestions
    }


def generate_ats_resume_pdf(data):
    """
    Generates an ATS-Compliant, beautifully structured PDF resume using ReportLab.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm,
        title=f"Resume - {data.get('name', 'Jobseeker')}",
        author="SkillNova AI ATS Builder"
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    header_name = ParagraphStyle(
        'HeaderName',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#084880'),
        alignment=TA_CENTER
    )
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#4A5568'),
        alignment=TA_CENTER
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#084880'),
        spaceBefore=8,
        spaceAfter=4
    )
    item_title = ParagraphStyle(
        'ItemTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1A202C')
    )
    item_sub = ParagraphStyle(
        'ItemSub',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#4A5568')
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2D3748')
    )

    story = []

    # Name and Contact
    story.append(Paragraph(data.get('name', 'Jobseeker').upper(), header_name))
    contact_line = f"{data.get('email', '')}  |  {data.get('phone', '')}  |  {data.get('location', 'India')}"
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(contact_line, contact_style))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=6))

    # Professional Summary
    target_role = data.get('preferred_role', 'Software Developer')
    summary_text = (
        f"Dedicated and performance-driven {target_role} with strong foundational knowledge and "
        f"hands-on project experience. Verified practical competency through AI-evaluated project benchmarks, "
        f"specializing in scalable architectures, problem-solving, and continuous learning."
    )
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_title))
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 3*mm))

    # Technical & Soft Skills
    story.append(Paragraph("TECHNICAL & PROFESSIONAL COMPETENCIES", section_title))
    tech_skills = data.get('technical_skills', [])
    soft_skills = data.get('soft_skills', [])
    if tech_skills:
        story.append(Paragraph(f"<b>Technical Skills:</b> {', '.join(tech_skills)}", body_style))
    if soft_skills:
        story.append(Paragraph(f"<b>Professional & Soft Skills:</b> {', '.join(soft_skills)}", body_style))
    story.append(Spacer(1, 3*mm))

    # Verified Skill Badges (SkillNova AI Exclusive Feature)
    verified_badges = data.get('verified_badges', [])
    if verified_badges:
        story.append(Paragraph("VERIFIED SKILL BADGES & CREDENTIALS", section_title))
        badge_text = "  ·  ".join([f"<b>{b.get('badge_name', 'Verified Skill')}</b> ({b.get('ai_score', 85)}% AI Score)" for b in verified_badges])
        story.append(Paragraph(badge_text, body_style))
        story.append(Spacer(1, 3*mm))

    # Projects
    projects = data.get('projects', [])
    if projects:
        story.append(Paragraph("KEY PROJECTS & VERIFIED OUTCOMES", section_title))
        for p in projects:
            if isinstance(p, dict):
                title = p.get('title', '')
                tech = p.get('technology', '')
                domain = p.get('domain', '')
            else:
                title = getattr(p, 'title', '')
                tech = getattr(p, 'technology', '')
                domain = getattr(p, 'domain', '')
            story.append(Paragraph(f"<b>{title}</b> — <font color='#4A5568'>{domain or 'Software Application'}</font>", item_title))
            if tech:
                story.append(Paragraph(f"<i>Technologies:</i> {tech}", item_sub))
            desc = getattr(p, 'architecture_notes', '') or f"Implemented core modules, ensured code quality, and validated system flow."
            story.append(Paragraph(f"· {desc}", body_style))
            story.append(Spacer(1, 2*mm))

    # Education
    educations = data.get('educations', [])
    if educations:
        story.append(Paragraph("EDUCATION", section_title))
        for edu in educations:
            if isinstance(edu, dict):
                deg = edu.get('degree', '')
                crs = edu.get('course', '')
                inst = edu.get('institution', '')
                cgpa = edu.get('cgpa')
                yr = edu.get('passing_year', '')
            else:
                deg = getattr(edu, 'degree', '')
                crs = getattr(edu, 'course', '')
                inst = getattr(edu, 'institution', '')
                cgpa = getattr(edu, 'cgpa', None)
                yr = getattr(edu, 'passing_year', '')
            edu_title = f"<b>{deg} in {crs}</b> - {inst}"
            extra = []
            if yr: extra.append(f"Graduated: {yr}")
            if cgpa: extra.append(f"CGPA: {cgpa}")
            extra_str = f" ({', '.join(extra)})" if extra else ""
            story.append(Paragraph(f"{edu_title}{extra_str}", body_style))
            story.append(Spacer(1, 1*mm))

    # Certifications
    certs = data.get('certifications', [])
    if certs:
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("CERTIFICATIONS", section_title))
        for c in certs:
            if isinstance(c, dict):
                name = c.get('name', '')
                org = c.get('organization', '')
                dt = c.get('issue_date', '')
            else:
                name = getattr(c, 'name', '')
                org = getattr(c, 'organization', '')
                dt = getattr(c, 'issue_date', '')
            cert_line = f"<b>{name}</b> - {org}" + (f" ({dt})" if dt else "")
            story.append(Paragraph(f"· {cert_line}", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
