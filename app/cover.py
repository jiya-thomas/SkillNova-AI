from io import BytesIO
from functools import lru_cache

from django.conf import settings
from llama_cpp import Llama

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import(SimpleDocTemplate, Paragraph, Spacer)
from reportlab.lib.units import mm

# ---- Load Model ----
@lru_cache(maxsize=1)
def get_llm():
    return Llama(
        model_path=str(settings.LLM_MODEL_PATH),
        n_ctx=2048,n_threads=4,n_batch=512,verbose=False
    )

# ---- Cover Letter Prompt ----
COVER_PROMPT="""
Write a professional cover letter for the job using only the provided information.

JOB:
Title: {title}
Company: {company}
Recipient: {recipient}

CANDIDATE:
Name: {name}
Qualification: {qualification}
Skills: {skills}

Rules:
- Return ONLY 3 short body paragraphs.
- DO NOT write "Dear {recipient}" or any greeting.
- DO NOT write the candidate's name as a heading.
- DO NOT write a subject line.
- DO NOT write a date.
- DO NOT write "Sincerely", "Regards", or any closing.
- Start directly with the first paragraph.
- Tailor the content to the specific job title and company.
- Naturally use relevant skills and qualification.
- Do not invent experience, certifications, achievements, or projects.
- Avoid generic repeated wording.
"""
def generate_ai_cover_letter(data):
    skills=", ".join(
        data.get("skills",[])
    )

    prompt=COVER_PROMPT.format(
        title=data.get("title", ""),company=data.get("company", ""),
        recipient=data.get("recipient", ""),name=data.get("name", ""),
        qualification=data.get("qualification", ""),skills=skills
    )

    response = get_llm().create_chat_completion(
        messages=[
            { "role":"user","content":prompt}
        ],
        temperature=0.4,max_tokens=500
    )

    return(
        response["choices"][0]["message"]["content"].strip()
    )

def generate_cover_letter(data):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize = A4, 
        rightMargin = 20*mm, leftMargin = 20*mm, 
        topMargin = 18*mm, bottomMargin = 18*mm,
        title="Cover Letter",
        author=data.get("name", "SkillNova AI"),
        subject=f"Cover Letter - {data.get('title', '')}",
        creator="SkillNova AI"
    )

    # ---- Paragraph Styles ----
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        'Name', fontSize=18, leading=22, spaceAfter=4,
        parent=styles['Heading1'],
        textColor=colors.HexColor('#084880')
    )
    normal_style = ParagraphStyle(
        "Normal", parent=styles["Normal"],
        fontSize=10.5, leading=16, spaceAfter=10,
    )
    subject_style = ParagraphStyle(
        "Subject", parent=styles["Normal"],
        fontSize=11, leading=15, spaceAfter=12,
    )

    story = []
    story.append(Paragraph(data['name'],name_style))
    story.append(Paragraph(f'{data['email']}|{data['phone']}',normal_style))
    story.append(Spacer(1,8))

    from datetime import date
    story.append(Paragraph(date.today().strftime("%B %d, %Y"),normal_style))
    story.append(
        Paragraph(f'{data["recipient"]}<br/>{data["company"]}',normal_style)
    )
    story.append(
        Paragraph(f'<b>Subject: Application for {data["title"]}</b>',subject_style)
    )
    story.append(Paragraph(f'Dear {data["recipient"]},',normal_style))
    skills = data["skills"]
    if skills:
        skill_text = ", ".join(skills)
    else:
        skill_text = "relevant technical and professional skills"

    # ---- Cover Letter ----
    ai_letter = generate_ai_cover_letter(data)
    for paragraph in ai_letter.split("\n\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(),normal_style))

    document.build(story)
    buffer.seek(0)
    return buffer

