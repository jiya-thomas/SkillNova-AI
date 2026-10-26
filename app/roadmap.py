import json, re
from functools import lru_cache

from django.conf import settings
from llama_cpp import Llama

# ---- Generative Prompt ----
ROADMAP_PROMPT = """
Create a learning roadmap for the target role using only skill-gap data.

ROLE: {role_name}

SKILL-GAP: {comparison}

Rules:
- Prioritize Missing, then Improving skills.
- Use Matched skills only as prerequisites.
- Order skills from basic to advanced.
- Create 3-5 phases.
- Phase Title: 2-4 words only.
- Do not include phase numbers or duration in titles.
- Each phase: relevant skills + 2 Courses + 1 Practice + 1 Project.
- Give activities short, specific, skill-related names.
- Practice = focused exercise; Project = buildable deliverable.
- Do not add skills outside skill-gap data.
- Set a realistic total duration based on skill gaps.
- Set realistic weekly study hours.
- Return JSON only.

JSON:
{{
    "duration":"X weeks",
    "effort":"X-X hrs/week",
    "phases":[
        {{
            "title": "Phase Title",
            "skills": ["Skill 1","Skill 2","Skill 3"],
            "activities":[
                {{"name":"Course 1","type":"Course"}},
                {{"name":"Course 2","type":"Course"}},
                {{"name": "Specific Exercise", "type": "Practice"}},
                {{"name": "Specific Mini Project", "type": "Project"}}
            ]
        }}
    ]
}}
"""

# ---- Load GGUF Model ----
@lru_cache(maxsize=1)
def get_llm():
    return Llama(
        model_path=str(settings.LLM_MODEL_PATH),
        n_ctx=2048, n_threads=4, 
        n_batch=512,verbose=False
    )

# ---- Generate Roadmap ----
def generate_roadmap(selected_role,comparison,role_name):
    # --- Skill-Gap Data ---
    skill_gap = [
        {
            "name":item["name"], "status":item["status"],
            "required":item["required"], "current":item["current"]
        }
        for item in comparison
    ]
    comparison_text = json.dumps(skill_gap,separators=(",",":")) 

    # ---- Create Prompt ----
    prompt = ROADMAP_PROMPT.format(
        role_name = role_name,comparison = comparison_text
    ) 

    # ---- Generate Roadmap ----
    response = get_llm().create_chat_completion(
        messages=[
            {"role":"user","content":prompt}
        ],
        temperature=0.1, max_tokens=700,
        response_format={"type":"json_object"}
    )

    # ---- Extract Response ----
    raw_output = (
        response["choices"][0]["message"]["content"]
        .strip()
    )
    if raw_output.startswith("```"):
        raw_output = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            raw_output
        ).strip()


    # ---- Convert: JSON to Dictionary ----
    roadmap_data = json.loads(raw_output)


    # ---- Skill Lookup ----
    skill_status={
        item["name"].lower(): item 
        for item in comparison
    }
    phases=[]

    # ---- Process Phases ----
    for index,phase in enumerate(
        roadmap_data.get("phases",[]),start=1):
        phase_progress=[] 
        for skill in phase.get("skills",[]):
            item = skill_status.get(skill.lower())

            if item:
                required = item['required']
                current = item['current']
                if required:
                    progress = min(round(current / required * 100),100)
                else:
                    progress = 0
            else:
                progress = 0
            phase_progress.append(progress)  

        # ---- Phase Progress ----
        progress=(
            round(sum(phase_progress)/len(phase_progress))
            if phase_progress
            else 0
        ) 

        # ---- Phase Status ----
        if progress == 100:
            status="Complete" 
            color="success"
        elif progress > 0:
            status="Learning"
            color="secondary"
        else:
            status="Planned"
            color="danger"

        # ---- Activities ----
        activities=[
            (activity["name"],activity["type"],status)
            for activity in phase["activities"]
        ] 

        # ---- Store Phase ----
        phases.append({
            "number":index,"title":phase['title'],
            "color":color,"skills":phase['skills'],
            "status":status, "progressed": progress,
            "activity":activities
        })

        # ---- Overall Progress ----
        overall_progress=(
            round(
                sum(phase['progressed'] for phase in phases)/len(phases)
            )
            if phases
            else 0
        )

    return{
        "role": role_name,
        "duration": roadmap_data["duration"],
        "effort": roadmap_data["effort"],
        "progress": overall_progress,
        "phases": phases
    }




