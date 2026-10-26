import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from llama_cpp import Llama

QUESTION_PROMPT = """
Generate mock interview questions for a job candidate.

ROLE: {role}
INTERVIEW TYPE: {interview_type}
EXPERIENCE: {experience}

Rules:
- Generate exactly 5 questions.
- Questions must be relevant to the role.
- Match the interview type.
- Match the candidate's experience level.
- Cover different topics.
- Do not repeat questions.
- Generate 3 to 5 useful evaluation keywords for every question.
- Return JSON only.
- Do not include explanations or markdown.

JSON:
{{
    "questions": [
        {{
            "question": "Interview Question",
            "keywords": ["keyword1", "keyword2", "keyword3"]
        }}
    ]
}}
"""

@lru_cache(maxsize=1)
def get_question_llm():
    return Llama(
        model_path=str(settings.LLM_MODEL_PATH),
        n_ctx=2048,n_threads=4,
        n_batch=512,verbose=False
    )


def generate_questions(role, interview_type, experience):
    prompt = QUESTION_PROMPT.format(
        role=role,interview_type=interview_type,
        experience=experience
    )

    response = get_question_llm().create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=600
    )

    content = response["choices"][0]["message"]["content"].strip()
    content = content.replace("```json","").replace("```","").strip()
    result = json.loads(content)
    return result.get("questions",[])[:5]