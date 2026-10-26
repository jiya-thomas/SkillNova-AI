import re
from datetime import datetime

# Curated Industry Benchmark Competencies
DOMAIN_BADGE_MAP = {
    'python': 'Verified Python Developer','django': 'Verified Django Developer',
    'flutter': 'Verified Flutter Developer','react': 'Verified React Developer',
    'data': 'Verified Data Analyst','sql': 'Verified SQL Specialist',
    'full-stack': 'Verified Full-Stack Developer','ai': 'Verified AI Engineer'
}

def evaluate_project_submission(title, domain, technology,
repo_url="",live_url="",arch_notes=""):
    # ---- Project Information ----
    title_text = (title or '').strip().lower()
    domain_text = (domain or '').strip().lower()
    tech_text = (technology or '').strip().lower()
    architecture_text = (arch_notes or '').strip().lower()
    combined_text=(
        f"{title_text}" f"{domain_text}"
        f"{tech_text}" f"{architecture_text}"
    )

    # ---- Tech Stack Depth ----
    recognized_technologies = [
        'python','django','fastapi','flask','react',
        'javascript','typescript','flutter','dart','postgresql',
        'mysql','sqlite','mongodb','docker','rest api','graphql',
        'html','css','bootstrap','tailwind','nlp','pandas','scikit-learn',
    ]
    detected_tech = [
        tech for tech in recognized_technologies
        if tech in tech_text or tech in combined_text
    ]
    tech_score = min(25,max(10,len(detected_tech)*5))

    # ---- Project Implementation ----
    implementation_score = 10
    if title_text:
        implementation_score+=3
    if domain_text:
        implementation_score+=2
    if tech_text:
        implementation_score+=5
    if repo_url:
        implementation_score+=3
    if live_url:
        implementation_score+=2
    implementation_score = min(25,implementation_score)    

    # ---- Architecture & System Design ----
    arch_score = 12
    arch_keywords = [
        'database','model','api','schema','service',
        'controller','component','security','scalability',
        'state','auth','authentication','authorization',
    ]
    matched_architecture = [
        keyword for keyword in arch_keywords
        if keyword in combined_text
    ]
    arch_score += min(13,len(matched_architecture)*3)
    arch_score = min(25,arch_score)

    # ---- Delivery & Reproducibility ----
    delivery_score = 10
    if repo_url and (
        'github.com' in repo_url.lower() or 'gitlab.com' in repo_url.lower()
    ):
        delivery_score += 8

    if live_url and (
        'http://' in live_url.lower() or 'https://' in live_url.lower()
    ):
        delivery_score += 7  
    delivery_score = min(25,delivery_score)

    # ---- Final Evaluation ----
    total_score=(
        tech_score+implementation_score+arch_score+delivery_score
    ) 

    is_verified = total_score >= 60

    # ---- Badge Name ----
    badge_name = "Verified Software Developer"
    for key, badge_label in DOMAIN_BADGE_MAP.items():
        if key in tech_text or key in domain_text:
            badge_name = badge_label
            break   

    # Badge Level
    if total_score >= 85:
        badge_level = 'Advanced Practitioner'
    elif total_score >= 70:
        badge_level = 'Proficient Engineer'
    else:
        badge_level = 'Associate Developer'

    return {
        'total_score': total_score,
        'is_verified': is_verified,
        'badge_name': badge_name,
        'badge_level': badge_level,
        'analysis': {
            'tech_score': tech_score,
            'implementation_score': implementation_score,
            'arch_score': arch_score,
            'delivery_score': delivery_score,
        }
    }             


           


