import re
import math
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from llama_cpp import Llama

from .skillgap import normalize_text

@lru_cache(maxsize=1)
def get_minilm_model():
    """Load the configured MiniLM GGUF embedding model once per process."""
    model_path = Path(settings.MINILM_MODEL_PATH)
    if not model_path.is_file():
        raise FileNotFoundError(f"MiniLM GGUF model not found: {model_path}")
    return Llama(
        model_path=str(model_path),
        embedding=True,
        n_ctx=512,
        verbose=False,
    )


def cosine_similarity_vectors(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def get_embedding(model, text):
    text = normalize_text(text or "")
    if not text:
        return None
    if hasattr(model, "embed"):
        embedding = model.embed(text)
        if embedding and isinstance(embedding[0], list):
            return embedding[0]
        return embedding
    result = model.create_embedding(text)
    return result["data"][0]["embedding"]


def minilm_similarity(job_text, profile_text):
    if not job_text or not profile_text:
        return 0
    model = get_minilm_model()
    job_embedding = get_embedding(model, job_text)
    profile_embedding = get_embedding(model, profile_text)
    if not job_embedding or not profile_embedding:
        return 0
    similarity = cosine_similarity_vectors(job_embedding, profile_embedding)
    return round(max(0.0, min(1.0, similarity)) * 100)

def calculate_ai_suitability(profile, job_post):
    if not profile or not job_post:
        return {
            'score': 0,
            'matched_skills': [],
            'missing_skills': [],
            'verdict': 'Incomplete Profile',
            'verified_badges_count': 0
        }

    # ---- Candidate Data ----
    candidate_skills = [s.name.lower() for s in profile.skills.all()]
    candidate_projects = list(profile.projects.all())
    verified_projects = list(profile.verified_projects.filter(is_verified=True))
    
    # ---- Gather Job Data ----
    job_skills = [s.strip().lower() for s in job_post.required_skills.split(",")]
    job_text = f"{job_post.title} {job_post.description} {' '.join(job_skills)}".lower()

    # 1. Skill Match
    matched_skills = []
    missing_skills = []
    for skill in job_skills:
        clean_skill = normalize_text(skill)
        # Check in candidate skill list
        if any(clean_skill in cs or cs in clean_skill for cs in candidate_skills):
            matched_skills.append(skill.title())
            continue
        
        # Check in project technologies
        in_projects = any(clean_skill in (p.technology or "").lower() for p in candidate_projects)
        if in_projects:
            matched_skills.append(skill.title())
            continue

        missing_skills.append(skill.title())

    if job_skills:
        skill_score = (len(matched_skills) / len(job_skills)) * 100
    else:
        skill_score = 75

    # 2. Verified Project Multiplier (Abstract requirement: verified outcomes vs static resume)
    verified_bonus = 0
    if verified_projects:
        # Check if verified projects touch required skills
        matched_verified = 0
        for vp in verified_projects:
            vp_text = f"{vp.technology} {vp.title} {vp.domain}".lower()
            if any(js in vp_text for js in job_skills):
                matched_verified += 1
        verified_bonus = min(20, (len(verified_projects) * 5) + (matched_verified * 5))

    # 3. MiniLM Semantic Match: Job Description - Candidate Profile
    profile_summary = f"{profile.career.preferred_role if hasattr(profile, 'career') else ''} "
    profile_summary += " ".join(candidate_skills) + " "
    for p in candidate_projects:
        profile_summary += f"{p.title} {p.technology} {p.domain} "
    for vp in verified_projects:
        profile_summary += f"{vp.title} {vp.technology} {vp.badge_name} "

    similarity_score = 50
    try:
        if profile_summary.strip() and job_text.strip():
            similarity_score = minilm_similarity(job_text, profile_summary)
    except Exception:
        similarity_score = 50

    # 4. Final Weighted AI Suitability Score
    # 50% Skill Match + 25% MiniLM Semantic Match + 25% Verified Project Credential Bonus
    final_score = round((skill_score * 0.50) + (similarity_score * 0.25) + verified_bonus)
    final_score = max(10, min(99, final_score))

    # Match Verdict
    if final_score >= 85:
        verdict = "Exceptional Match"
    elif final_score >= 70:
        verdict = "Strong Match"
    elif final_score >= 50:
        verdict = "Moderate Match"
    else:
        verdict = "Developing Match"

    return {
        'score': final_score,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'verdict': verdict,
        'verified_badges_count': len(verified_projects)
    }
