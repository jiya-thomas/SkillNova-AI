import pymupdf, re
import numpy as np 
from io import BytesIO

from .models import Project
from .resume import ResumeParser

from django.conf import settings
from llama_cpp import Llama


# ---- MiniLM Embedding Model ----
_embedding_model = None

def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = Llama(
            model_path=str(settings.MINILM_MODEL_PATH),
            embedding=True,verbose=False
        )
    return _embedding_model    

# --- Job Role Skills --- 
ROLE_SKILLS={
    # Python Developer
    'python':{
       "Python":5,"Django":5,"SQL":4,
       "Git":3,"JavaScript":3, 
    },
    # React Developer
    'react':{
        "JavaScript":5,"React":5,"HTML":4,
        "CSS":4,"REST API":4,
    },
    # Laravel Developer
    'laravel':{
        "PHP":5,"Laravel":5,"MySQL":4,
        "REST API":3,"MVC":4
    },
    # Flutter Developer
    'flutter':{
        "Dart":5,"Flutter":5,"Firebase":4,
        "REST API":3,"UI/UX":3,
    },
    # Data Analyst
    'data':{
        "Python":4,"SQL":5,"Excel":5,"Pandas":4,
        "NumPy":3,"Statistics":4,
    }
}

# ------ PDF Extraction ------
def extract_pdf_text(pdf_bytes):
    text = ""
    document = pymupdf.open(
        stream=pdf_bytes,filetype='pdf'
    )
    for page in document:
        text += page.get_text('text')+"\n"
    document.close()
    return text   

# ------ Text Normalization ------
def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"[^a-z0-9+#./\- ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ------ Sentence Extraction ------
def split_sentences(text):
    text = normalize_text(text)
    sentences = re.split(r"(?<=[.!?])\s+", text)  
    return[
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

# ------ Mini-LM Semantic Similarity ------
def calculate_similarity(skill,sentences):
    if not sentences:
        return 0.0

    model = get_embedding_model() 
    skill_embedding = np.asarray(
        model.embed(skill,normalize=True),dtype=np.float32
    )  
    max_similarity = 0.0

    for sentence in sentences:
        sentence_embedding = np.asarray(
            model.embed(sentence,normalize=True),
            dtype=np.float32
        )  
        similarity = float(
            np.dot(skill_embedding,sentence_embedding)
        ) 
        max_similarity=max(
            max_similarity,similarity
        )  
    return max_similarity           

# ------ Skill Extraction
def extract_skills(text,required_skills):
    normalized_text = normalize_text(text)
    sentences = split_sentences(normalized_text)
    found_skills = []

    for skill in required_skills:
        skill_lower = normalize_text(skill)

        # Level 1: Exact Skill Match
        pattern = r"\b" + re.escape(skill_lower) + r"\b"
        if re.search(pattern,normalized_text):
            found_skills.append(skill)
            continue

        # Level 2: MiniLM Semantic Similarity
        similarity = calculate_similarity(skill_lower,sentences)
        if similarity >= 0.45:
            found_skills.append(skill)
    return found_skills

# ------ Skill Confidence ------
def get_skill_confidence(text,skill):
    normalized_text = normalize_text(text)
    pattern = r"\b" + re.escape(normalize_text(skill)) + r"\b"

    if re.search(pattern,normalized_text):
        return 1.0
    sentences = split_sentences(normalized_text)
    return calculate_similarity(skill,sentences)


# ------ Skill-Gap Analysis ------
def analyze_skill_gap(pdf_bytes, selected_role):
    resume_text = extract_pdf_text(pdf_bytes)

    # ---- Resume Project Extraction ----
    parser = ResumeParser(BytesIO(pdf_bytes))
    parsed_resume = parser.parse()
    projects = parsed_resume.get('projects',[])

    # ---- Project Technology & Description ----
    project_text = " ".join(
        f"{project.get('technology','')} "
        f"{project.get('description','')}"
        for project in projects
    )

    required_skills = ROLE_SKILLS.get(selected_role,{})
    resume_skills = extract_skills(resume_text,required_skills.keys())
    project_skills = extract_skills(project_text,required_skills.keys())
    comparison = []
    matched = improving = missing = 0

    for skill, required_level in required_skills.items():
        in_resume = skill in resume_skills
        in_project = skill in project_skills

        confidence = get_skill_confidence(resume_text,skill)

        if not in_resume:
            current_level = 0
        elif in_resume and not in_project:
            current_level = max(1,round(2*confidence))
        else:
            current_level = min(
                required_level, max(1,round(2+(2*confidence)))
            )

        if current_level >= required_level:
            status = 'matched'
            matched += 1
        elif current_level > 0:
            status = 'improving'
            improving += 1
        else:
            status = 'missing' 
            missing += 1                  

        # Skill Gap Percentage
        gap_percent = round(
            ((required_level-current_level)/required_level*100)
        )
        
        comparison.append({
            'name':skill,'required':required_level,
            'current':current_level,'status': status,
            'gap':gap_percent,'resume':in_resume, 
            'project':in_project, 'confidence': round(confidence*100)
        }) 

    # ---- Weighted Match Score ----
    total_weight = sum(required_skills.values())

    # Resume Score
    resume_weight = sum(
        required_skills[skill]
        for skill in required_skills
        if skill in resume_skills
    )
    resume_score = (
        round((resume_weight/total_weight)*100)
        if total_weight else 0
    )

    # ---- Project Evidence Score ----
    if projects:
        project_weight = sum(
            required_skills[skill]
            for skill in required_skills
            if skill in project_skills
        )
        project_score = (
            round((project_weight/total_weight)*100)
            if total_weight else 0
        )
    else: project_score = None

    # ---- Overall Score ----
    if project_score is None:
        score = resume_score
    else:
        score = round((resume_score * 0.70)+(project_score * 0.30))     

    return{
        'score':score,'project_score':project_score,
        'matched':matched,'improving':improving,'missing':missing,
        'total':len(required_skills),'comparison':comparison,
        "resume_skills": resume_skills,"project_skills": project_skills,
        'projects':projects, 'projects_count':len(projects), 'resume_score': resume_score,
    }    




          