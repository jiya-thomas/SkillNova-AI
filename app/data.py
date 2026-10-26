# Role: Jobseeker (url, title, icon, active_urls)
stud_menu=[
    ("jobseeker", "Dashboard", "fa-home", ["jobseeker"]),
    ("skillgap", "Skill Gap Analysis", "fa-chart-line", ["skillgap"]),
    ("roadmap", "Learning Roadmap", "fa-graduation-cap", ["roadmap"]),
    ("ats_resume", "ATS Resume", "fa-file-lines", ["ats_resume"]),
    ("project_verify", "Skill Verification", "fa-medal", ["project_verify","skillbadge"]),
    ("jobs", "Job Portal", "fa-briefcase", ["jobs","applied","invitations"]),
    ("cover", "AI Cover Letter", "fa-file-pen", ["cover"]),
    ("interview", "Mock Interview", "fa-microphone", ["interview", "session", "analysis"]),
]

# Role: Recruiter (url, title, icon, active_urls)
comp_menu=[
    ("recruiter", "Dashboard", "fa-home", ["recruiter"]),
    ("candidate", "Candidates", "fa-users", ["candidate", "candidate_detail"]),
    ("listing", "Job Listings", "fa-briefcase", ["listing", "postJob"]),
    ("screening", "AI Screening", "fa-bullseye", ["screening"]),
    ("applications", "Applications", "fa-clipboard-list", ["applications"]),
    ("interviews", "Interviews", "fa-calendar-alt", ["interviews"]),
]

admin_menu = [
    ('admin', 'Dashboard', 'fa-home',['admin']),
    ('admin', 'User Management', 'fa-users',['']),
    ('admin', 'Job Management', 'fa-briefcase',['']),
    ('admin', 'Skill Management', 'fa-code',['']),
    ('admin', 'Analytics', 'fa-chart-pie',['']),
    ('admin', 'Reports', 'fa-file-alt',['']),
]

# Skill Gap: (Name, value)
skill_gap=[
    ("Frontend","35"),("Backend","25"),('Database',"45")
]
# Roadmap: (Name, status)
skillset=[
    ("Python","complete"),("React","learning"),
    ("Javascript","upcoming")
]
# Career Readiness
career_insight=[
    ("Technical Skills","88%"),("Interview","78%"),
    ("Projects","82%"),("Resume","85%")
]

# Location
state=["Kerala","TamilNadu"]; country=["India"]

# Degree
degrees=["Bachelor's","Master's"]
courses=["B.Tech","M.Tech","BCA","MCA"]

# Skills
tskills=["Python","Django","JavaScript","Flutter","React","SQL",'bootstrap','React Native',
        'Node JS','ExpressJS','PHP','MySQL','PostgreSQL','Mongodb']
sskills=["Communication","Teamwork","Leadership","Reasoning","Adaptibility"]

# Career
role={
    "Python Developer":"python","React Developer":"react","Data Analyst":"data",
    "Laravel Developer":"laravel","Flutter Developer":"flutter"
}

# Domain
domains={
   'Frontend Development':'frontend','Backend Development':'backend',
   'Full-Stack Development':'full-stack','Data Analytics & NLP':'data',
   'IoT Development':'iot' 
}

# Work Locations
location=["Trivandrum","Kochi","Chennai","Banglore"]
work=["Onsite","Hybrid","Remote"]

# Job Status
status=[
    ('applied', 'Applied'),('shortlisted', 'Shortlisted'),
    ('scheduled', 'Interview'),
    ('rejected', 'Rejected'),('selected', 'Selected')
]

# Date
date=[
    ('week','Last 7 days'),('month','Last 30 days')
]

# Interview
interview_type=[
    ("technical","Technical Level"),("hr","HR Level")
]

# Job Listing
job_list=[
    {
        "id":1,"title":"Python Developer", "company":"Infosys Limited",
        "location":"Thiruvanathapuram", "mode":"Hybrid", 
        "type":"Full Time", "experience":"0-2 years",
        "skills": ["Python", "Django", "SQL", "Git"],
        "qualification": ["B.Tech CS", "MCA"], "deadline":"30 August 2026",
        "opening":20,"status":'Active'
    }
]

# Interview Questions


# AI-Match Data
ai_match={
    'Python':70,'Django':81,'SQL':60,'Javascript':72
}

# AI-Matched Candidates
ai_candidate=[
    ('Ankush Jain','Python Developer','90%'),
    ('Sam Thomas','React Developer','85%'),
    ('Arun Naidu','PHP Developer','80%'),
    ('William Tom','Flutter Developer','89%')
]

# Recruitement Applications
job_application=[
    ("Applications","20"),("Shortlisted","10"),
    ("Interviewed","5"),("Selected","3")
]

# Job Openings
job_opening=[
    ("Python Developer",4),("PHP Developer",2),
    ("Java Developer",10),("Java Developer",12)
]

# Experience
experience={
    'Fresher':'fresher','0-2 years':'entry',
    '3-5 years':'mid','5+ years':'senior'
}

# Candidates
candid_list=[
    {
        "id": 1, "name": "Rahul Kumar",
        "role": "Python Developer",
        "qualification": "MCA (integrated)",
        "experience": "2 Years",
        "skills": ["Python", "Django", "SQL"],
    }
]

# Recent Activity
recent_activity=[
    ('Jiya Thomas','ATS Optimization','ATS',10),
    ('Arun Raj','New Job Posted','Jobs',24),
    ('Rahul Kumar','Skill Gap Analysis','Skill Gap',42),
    ( 'Anjali Menon','Account Created','Users',1)
]
