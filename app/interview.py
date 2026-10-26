import math, re
from functools import lru_cache
from pathlib import Path
from .questions import generate_questions

from django.conf import settings
from llama_cpp import llama


def clean_text(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ",text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def keyword_score(answer,keywords):
    answer = clean_text(answer)
    matched_keywords = []

    for keyword in keywords:
        keyword = clean_text(keyword)
        if keyword in answer:
            matched_keywords.append(keyword)

    if not keywords:
        return 0, matched_keywords
    score = (len(matched_keywords)/len(keywords))*100
    return round(score), matched_keywords

@lru_cache(maxsize=1)
def get_minilm_model():
    model_path = Path(settings.MINILM_MODEL_PATH)

    if not model_path.exists():
        raise FileNotFoundError(
            f"GGUF Model not found:{model_path}"
        )

    return Llama(
        model_path = str(model_path),
        embedding=True, n_ctx=512, verbose=False
    ) 

# Cosine Similarity
def cosine_similarity(vector_a, vector_b):
    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )   
    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )
    magnitude_b = math.sqrt(
        sum(b*b for b in vector_b)
    )
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)   

# ---- MiniLM Semantic Similarity ----
def miniml_score(answer, keywords):
    answer = clean_text(answer)
    keyword_text = clean_text(" ".join(keywords))

    if not answer or not keyword_text:
        return 0, False

    model = get_minilm_model()

    result = model.create_embedding([answer, keyword_text])
    answer_embedding = result["data"][0]["embedding"]
    keyword_embedding = result["data"][1]["embedding"]  

    similarity = cosine_similarity(answer_embedding, keyword_embedding)
    similarity = max(0.0, min(1.0, similarity))

    similarity_percentage = rounf(similarity*100)
    threshold = float(
        getattr(settings,'ATS_SEMANTIC_THRESHOLD',0.55)
    )
    semantic_match = similarity >= threshold

    return similarity_percentage, semantic_match    

def evaluate_answer(answer, question_data):
    keywords = question_data.get('keywords',[])
    
    keyword_percentage, matched_keywords=keyword_score(answer,keywords)
    
    similarity_percentage, semantic_match = miniml_score(answer, keywords) 
    
    final_score = (keyword_percentage*0.70 + similarity_percentage*0.30)
 
    missing_keywords = [
        keyword
        for keyword in keywords
        if clean_text(keyword) not in matched_keywords
    ]

    return{
        "score": round(final_score), 
        "keyword_score": keyword_percentage,
        "semantic_match":semantic_match,
        "similarity_score": similarity_percentage,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords
    }

def calculate_overall_score(scores):
    if not scores:
        return 0
    return round(sum(scores) / len(scores))

def analyze_interview(answers, questions):
    question_results = []; scores = [] 
    keyword_scores = []; similarity_scores = [] 

    total_keywords = total_matched = 0
    strong_answers = good_answers = improve_answers = 0
    
    for question, answer in zip(questions, answers):
        result = evaluate_answer(answer,question)
        question_results.append(result)
        scores.append(result["score"])
        keyword_scores.append(result["keyword_score"])
        similarity_scores.append(result["similarity_score"])

        total_keywords += len(question.get("keywords",[]))
        total_matched += len(result["matched_keywords"])

        if result["score"] >= 80:
            strong_answers += 1
        elif result["score"] >= 60:
            good_answers += 1  
        else:
            improve_answers += 1      

    overall_score = calculate_overall_score(scores)
    keyword_score = calculate_overall_score(keyword_scores)
    similarity_score = calculate_overall_score(similarity_scores)

    if total_keywords:
        skill_coverage = round( (total_matched / total_keywords) * 100)
    else:
        skill_coverage = 0

    return {
        "overall_score": overall_score,
        "keyword_score": keyword_score,
        "similarity_score": similarity_score,
        "skill_coverage": skill_coverage,
        "question_results": question_results
    }            
