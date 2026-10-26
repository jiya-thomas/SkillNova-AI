from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.http import FileResponse, JsonResponse
from django.db import models
from django.db.models import Q
from django.utils import timezone
from .models import RoleUser
from .data import *
from functools import wraps

from .resume import ResumeParser
from .skillgap import analyze_skill_gap
from .roadmap import generate_roadmap
from .cover import generate_cover_letter
from .interview import evaluate_answer, calculate_overall_score
from .questions import generate_questions
from .ats import analyze_resume_for_ats, generate_ats_resume_pdf
from .verification import evaluate_project_submission
from .screening import calculate_ai_suitability
import re, random, pymupdf
from .models import (RoleUser,Profile,Education,Career,Location,
    Skill,Project,Certification,JobPost,JobApplication,ProjectVerification,InterviewSchedule)

# Session Handling 
def login_required(view_func):
    @wraps(view_func)
    def wrapper(request,*args,**kwargs):
        if not request.session.get("user_id"):
            messages.error(request, "Please login first.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper

def layout(request):
    email = request.session.get("user_email")
    current_user = RoleUser.objects.get(email=email)
    return render(request,'layout.html')

# ---- User Registration ----
def register(request):
    if request.method == 'POST':
        name=request.POST['name']
        email=request.POST['email']
        phone=request.POST['phone']
        role=request.POST['role']
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']

        # Check Password
        if password != confirm_password:
            messages.error(request,"Passwords do not match.")
            return redirect('register')
        
        # Check Email
        if RoleUser.objects.filter(email=email).exists():
            messages.error(request,"Email already registered.")
            return redirect('register')
        
        # Create User
        user=RoleUser.objects.create(
            name=name, email=email, phone=phone,
            role=role, password=password
        )
        print("REGISTERED USER ID:", user.id)
        print("REGISTRATION DATABASE:", user._state.db)
        print("USER EXISTS AFTER REGISTRATION:",
            RoleUser.objects.filter(
                email=email,role=role
            ).exists()
        )

        messages.success(request,"Account Created Successfully.")
        return redirect('login')
    return render(request, "register.html")

# ---- User Login ----
from django.db import connection
def login(request): 

    print("DATABASE:", connection.settings_dict["NAME"])  
    if request.method=='POST':
        email=request.POST['email']
        password=request.POST['password']
        role=request.POST['role'] 

        print("LOGIN EMAIL:", email)
        print("LOGIN ROLE:", role)

        print("USER EXISTS:",
            RoleUser.objects.filter(
                email=email, role=role
            ).exists()
        )

        try:
            user=RoleUser.objects.get(email=email, role=role)
            if user.password==password:
                request.session["user_id"] = user.id
                request.session["name"] = user.name.split()[0]
                request.session["role"] = user.role
                # Role: Student
                if user.role == 'jobseeker':
                    return redirect("jobseeker")
                if user.role == 'recruiter':
                    return redirect("recruiter")
                if user.role == 'admin':
                    return redirect('admin')    
                return redirect('home')
            else: messages.error(request, "Invalid password.")
        except RoleUser.DoesNotExist:
            messages.error(request, "Invalid User Credentials.")       
    return render(request,'login.html')

# ---- User Logout ----
def logout(request):
    request.session.flush()
    messages.success(request,"Logout Successfull")
    return redirect('login')

# ---- Home Page ----
def home(request):
    return render(request,"index.html")

# ---- Jobseeker ----
@login_required
def jobseeker(request):
    user_id = request.session.get("user_id")
    user = get_object_or_404(RoleUser, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=user)
    total_projects = profile.projects.count()
    verified_badges_count = profile.verified_projects.filter(is_verified=True).count()
    total_applications = user.job_applications.count()
    ats_score = request.session.get("last_ats_score", 78)
    verified_badges = profile.verified_projects.filter(is_verified=True).order_by('-created_at')[:4]
    
    # Calculate career readiness
    career_insight_dynamic = [
        ("Technical Skills", "88%"),
        ("Interview Ready", "82%"),
        ("Verified Projects", f"{verified_badges_count}"),
        ("Active Applications", f"{total_applications}")
    ]
    
    context={
        "menu": stud_menu,
        "skill": skill_gap,
        "skillset": skillset,
        "career_insight": career_insight_dynamic,
        "name": 'Skill Nova AI | Student',
        "user": user,
        "profile": profile,
        "total_projects": total_projects,
        "verified_badges_count": verified_badges_count,
        "total_applications": total_applications,
        "ats_score": ats_score,
        "verified_badges": verified_badges,
    }
    return render(request,'jobseeker/jobseeker.html',context)

# ---- Clean Skills ----
def clean_skills(skills):
    cleaned = []
    for skill in skills or []:
        if not isinstance(skill, str):
            continue
        skill = skill.strip()

        # Remove empty and duplicate skills
        if skill and skill.lower() not in [
            item.lower() for item in cleaned
        ]:
            cleaned.append(skill)
    return cleaned   
  
# ---- User Profile ----
@login_required
def profile(request):
    # Fetch User
    user = get_object_or_404(
        RoleUser, id = request.session.get('user_id')                     
    )

    # ---- Sections ----
    profile, _ = Profile.objects.get_or_create(user=user)
    education, _ = Education.objects.get_or_create(profile=profile)
    career, _ = Career.objects.get_or_create(profile=profile) 

    # ---- Profile Section ----
    state_name = profile.state
    country_name = profile.country

    # ---- Education ----
    institution = education.institution
    degree = education.degree
    course = education.course
    percentage = education.percentage
    cgpa = education.cgpa
    passing_year = education.passing_year

    # ---- Career ----
    preferred_role = career.preferred_role
    preferred_locations = list(career.locations.values_list(
        'name',flat=True))
    expected_salary = career.expected_salary
    work_mode = career.work_mode

    # ---- Skills ----
    technical = tskills
    soft = sskills
    technical_skills = list(profile.skills.filter(
        skill_type='technical').values_list('name',flat=True)
    )
    soft_skills =  list(profile.skills.filter(
        skill_type="soft") .values_list("name", flat=True) 
    )

    # ---- Portfolio ----
    projects = profile.projects.all()
    certifications = profile.certifications.all( )

    # ---- Resume Extraction ----
    resume_data = None
    if request.method == 'POST':
        pdf_file = request.FILES.get('resume')
        if pdf_file:
            try:
                parser = ResumeParser(pdf_file)
                resume_data = parser.parse()
                messages.success(request,"Resume Uploaded Successfully !")
            except Exception:    
                messages.error(request,"Resume Upload Failed !")
                resume_data = None

    # ---- Apply Extracted Resume Data ----
    if resume_data:
        # Education
        education_data = resume_data.get('education',{})
        institution = (education_data.get("institution") or institution )
        degree = ( education_data.get("degree") or degree ) 
        course = ( education_data.get("course") or course )
        cgpa = ( education_data.get("cgpa") or cgpa ) 
        percentage = ( education_data.get("percentage") or percentage )
        passing_year = ( education_data.get("passing_year") or passing_year )

        # Skills
        skills_data = resume_data.get( "skills", {} ) 
        resume_technical = skills_data.get( "technical", [] ) 
        resume_soft = skills_data.get( "soft", [] )
        if resume_technical:
            technical_skills = clean_skills(resume_technical)
        if resume_soft:
            soft_skills = clean_skills(resume_soft)

        # Projects
        resume_projects = resume_data.get( "projects", [] ) 
        if resume_projects: 
            projects = resume_projects

        # Certificates
        resume_certifications = resume_data.get( "certificates", [] ) 
        if resume_certifications: 
            certifications = resume_certifications

    # ---- Template Context ----
    context={
        "menu": stud_menu,"resume_data": resume_data,
        'user': user, 'profile': profile, "states": state, 
        "nation": country, "degrees": degrees, "courses": courses, 
        "roles": role, "place": location, "work": work,
        "state_name": state_name, "country_name": country_name,
        "institution": institution, "degree": degree, "course": course, 
        "cgpa": cgpa, "percentage": percentage, "passing_year": passing_year,
        "preferred_role": preferred_role, "preferred_location": preferred_locations, 
        "work_mode": work_mode, "salary": expected_salary,"technical": technical,
        "soft": soft, "technical_skills": technical_skills, "soft_skills": soft_skills, 
        "projects": projects, "certifications": certifications,
    }         
    return render(request,"jobseeker/profile.html",context)

# ---- Save Profile ----
@login_required
def save_profile(request):
    if request.method != 'POST':
        return redirect('profile')
    print("CGPA received:", request.POST.get("cgpa"))
    user_id=request.session.get('user_id')
    user=get_object_or_404(RoleUser,id=user_id) 
    profile,_=Profile.objects.get_or_create(user=user)

    # Profile
    profile.state=request.POST.get('state','').strip()
    profile.country=request.POST.get('country','').strip()
    if request.FILES.get('image'):
        profile.profile_image=request.FILES['image']
    profile.save()   

    # Education
    education,_=Education.objects.get_or_create(profile=profile)
    education.institution=request.POST.get('institution','').strip()
    education.degree = request.POST.get('degree', '').strip() 
    education.course = request.POST.get('course', '').strip()
    education.cgpa = request.POST.get('cgpa') or None
    education.percentage = request.POST.get('percentage') or None
    education.passing_year = request.POST.get('year') or None
    education.save()
    print("CGPA after save:", education.cgpa)

    # Career
    career,_=Career.objects.get_or_create(profile=profile)
    career.preferred_role = request.POST.get('role','').strip()
    career.work_mode = request.POST.get('work_mode','').strip()
    career.expected_salary = (request.POST.get('salary') or None)
    
    locations=request.POST.getlist('locations')
    location_objects=[]
    for loc_name in locations:
        loc_name = loc_name.strip()
        if loc_name:
            location,_=Location.objects.get_or_create(name=loc_name)
            location_objects.append(location)
    career.locations.set(location_objects)          
    career.save()

    # Skills
    technical=request.POST.getlist('technical')
    soft=request.POST.getlist('soft')
    Skill.objects.filter(profile=profile).delete()

    for skill in technical:
        skill=skill.strip()
        if skill:
            Skill.objects.create(profile=profile,name=skill,skill_type='technical')

    for skill in soft:
        skill=skill.strip()
        if skill:
           Skill.objects.create(profile=profile,name=skill,skill_type='soft')  

    # Projects
    project_title=request.POST.getlist('project_title') 
    project_domain=request.POST.getlist('project_domain')
    project_technology=request.POST.getlist('project_tech')
    Project.objects.filter(profile=profile).delete()   

    for title,domain,technology in zip(project_title,project_domain,project_technology):
        title=title.strip()
        domain=domain.strip()
        technology=technology.strip()
        if title:
            Project.objects.create(
                profile=profile,title=title,domain=domain,technology=technology
            )

    # Certifications
    cert_name=request.POST.getlist('cert_name')
    cert_org=request.POST.getlist('cert_org') 
    cert_date=request.POST.getlist('cert_date')
    Certification.objects.filter(profile=profile).delete()

    for name,organization,issue_date in zip(cert_name,cert_org,cert_date):
        name=name.strip()
        organization=organization.strip()
        issue_date=issue_date.strip()
        if name:
            Certification.objects.create(
                profile=profile,name=name,organization=organization,issue_date=issue_date
            )

    messages.success(request,'Profile saved successfully!')
    return redirect('profile')

# ---- Skill-Gap ----
@login_required
def skill(request):
    context={"menu":stud_menu,"roles":role.items(),'score':0,'matched':0,
            'improving':0,'missing':0,'total':0,'compare':[],'selected_role':None}
    if request.method == 'POST':
        selected_role = request.POST.get('target_role')
        resume = request.FILES.get('resume')
        context['selected_role'] = selected_role

        if resume and selected_role:
            user_id = request.session.get("user_id")
            user = RoleUser.objects.get(id=user_id)
            profile = user.profile
            projects = profile.projects.all()
            project_tech = " ".join(
                project.technology
                for project in projects
                if project.technology
            )
            result = analyze_skill_gap(resume.read(),selected_role)
            context.update({
                'score':result['score'],'matched':result['matched'],
                'improving':result['improving'],'missing':result['missing'],
                'total':result['total'],'compare':result['comparison']
            })
            request.session["skillgap"] = {
                "role": selected_role,"comparison": result["comparison"]
            }
            request.session.pop('roadmap',None)
            messages.success(request,"Skill Gap Analysis completed successfully")
        else:
            messages.warning(request,"Please select a role and upload resume")    
    return render(request,"jobseeker/skillgap.html",context)

# ---- Learning Roadmap ----
@login_required
def roadmap(request):
    skillgap = request.session.get('skillgap')
    if not skillgap:
        return render(
            request,'jobseeker/roadmap.html',
            {'menu':stud_menu, 'roadmap':None}
        )
    selected_role = skillgap['role']

    cached_roadmap = request.session.get('roadmap')
    if(cached_roadmap and cached_roadmap.get('role')==selected_role):
        roadmap_data = cached_roadmap['data']
    else:
        role_name = next(
            (name for name, value in role.items()
            if value == selected_role),
            selected_role
        )
        comparison = skillgap['comparison']
        roadmap_data = generate_roadmap(selected_role,
            comparison,role_name)
        request.session['roadmap']={
            'role': selected_role,'data': roadmap_data
        }
    
    context={"menu":stud_menu,"roadmap":roadmap_data}
    return render(request,"jobseeker/roadmap.html",context)

# ---- Cover Letter ----
@login_required
def cover(request):
    if request.method == 'POST':
        selected_skills = request.POST.getlist('skills')
        data={
            'title':request.POST.get('title'),
            'company':request.POST.get('company'),
            'recipient':request.POST.get('recipient'),
            'name':request.POST.get('fullname'),
            'email':request.POST.get('email'),
            'phone':request.POST.get('phone'),
            'qualification': request.POST.get('qualification'),
            "skills": selected_skills,
        }
        if not all(data.values()):
            messages.error(request, "Please fill in all the required fields.")
            return render(request, "jobseeker/cover.html",
                {"menu": stud_menu, "skills": tskills})
        pdf = generate_cover_letter(data)
        return FileResponse(
            pdf, as_attachment=False,filename="cover_letter.pdf"
        )   
    context={"menu":stud_menu,"skills":tskills}
    return render(request,"jobseeker/cover.html",context)

# ---- Job Portal ----
@login_required
def jobs(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser,id=user_id)
    profile,_ = Profile.objects.get_or_create(user=user)
    jobs = JobPost.objects.filter(status='Active')

    # Filter Fields
    search = request.GET.get("search","").strip()
    location = request.GET.get("location","").strip()
    experience_q = request.GET.get("experience","").strip()
    mode = request.GET.get("mode","").strip()

    if search:
        jobs = jobs.filter(
            Q(title__icontains=search)|
            Q(company_name__icontains=search)|
            Q(required_skills__icontains=search)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if experience_q:
        jobs = jobs.filter(experience__icontains=experience_q)
    if mode:
        jobs = jobs.filter(work_mode__iexact=mode)            

    for job in jobs:
        job.skills_list=[
            skill.strip()
            for skill in job.required_skills.split(",")
            if skill.strip()
        ]
    applied_job = JobApplication.objects.filter(candidate=user
    ).values_list('job_id',flat=True) 

    context={
        "menu":stud_menu,"jobs":jobs,"profile":profile,
        "applied":applied_job,"locations":location,
        "experience":experience.items(),"works":work,
        "search_q":search,"loc_q":location,
        "exp_q":experience_q,"mode_q":mode
    }       
    return render(request, "jobseeker/jobs.html", context)

# ---- Apply for Job ----
@login_required
def apply_job(request, job_id):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user = get_object_or_404(RoleUser, id=user_id)
        profile, _ = Profile.objects.get_or_create(user=user)
        job = get_object_or_404(JobPost, id=job_id)
        
        app, created = JobApplication.objects.get_or_create(job=job, candidate=user)
        if not created:
            messages.info(request, f"You have already applied for {job.title} at {job.company_name}.")
            return redirect('applied')
            
        cover_note = request.POST.get('message', '').strip()
        suitability = calculate_ai_suitability(profile, job)
        
        app.cover_note = cover_note
        app.ai_suitability_score = suitability['score']
        app.matched_skills = ", ".join(suitability['matched_skills'])
        app.missing_skills = ", ".join(suitability['missing_skills'])
        app.status = 'applied'
        app.save()
        
        messages.success(request, f"Application submitted! AI Suitability Match Score: {suitability['score']}%")
        return redirect('applied')
    return redirect('jobs')

# ---- My Applications ----
@login_required
def applied(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    applications = JobApplication.objects.filter(candidate=user).select_related('job', 'job__recruiter').order_by('-applied_at')
    
    context = {
        "menu": stud_menu,"applied": applications,"date":date,
        "works":work,"status":status
    }
    return render(request, "jobseeker/applications.html", context)

# ---- Interview Invitation ----
def invitations(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    interviews = InterviewSchedule.objects.filter(candidate=user).select_related('application', 'recruiter')
    context={"menu":stud_menu,"interviews":interviews}
    return render(request,'jobseeker/invitation.html',context)

# ---- Jobseeker: ATS Resume Optimizer & Builder ----
@login_required
def ats_resume(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=user)
    candidate_skills = list(
        profile.skills.values_list('name', flat=True)
    )

    analysis_result = None
    selected_role = "python"

    if request.method == 'POST':
        selected_role = request.POST.get('target_role','python')
        custom_jd = request.POST.get('custom_jd','').strip()
        pdf_file = request.FILES.get('resume_file')
        resume_text = ""

        # Extract uploaded PDF text
        if pdf_file:
            try:
                doc = pymupdf.open(stream=pdf_file.read(),filetype='pdf')
                for page in doc:
                    resume_text += page.get_text('text') + "\n"
                doc.close()

            except Exception:
                messages.warning(
                    request,
                    "Could not parse uploaded PDF file. "
                    "Using current profile data instead."
                )

        # Profile fallback
        if not resume_text.strip():
            edu_text = " ".join(
                f"{e.degree} {e.course} {e.institution}"
                for e in profile.educations.all()
            )
            proj_text = " ".join(
                f"{p.title} {p.technology} {p.domain}"
                for p in profile.projects.all()
            )
            cert_text = " ".join(
                f"{c.name} {c.organization}"
                for c in profile.certifications.all()
            )

            resume_text = (
                f"{user.name} " f"{user.email} " 
                f"{user.phone} " f"{edu_text} " 
                f"{proj_text} "  f"{cert_text} "
                f"{' '.join(candidate_skills)}"
            )

        # ---- ATS + MiniLM Analysis ----
        analysis_result = analyze_resume_for_ats(
            resume_text=resume_text,
            target_role=selected_role,
            job_description=custom_jd,
            profile_skills=candidate_skills
        )

        request.session['last_ats_score'] = (
            analysis_result['score']
        )

        messages.success(request,f"ATS Analysis Completed! ")

    context = {
        "menu": stud_menu,"roles": role.items(),
        "selected_role": selected_role,
        "analysis": analysis_result,
        "user": user,"profile": profile,
        "candidate_skills": candidate_skills
    }

    return render(request,"jobseeker/resume.html",context)

# ---- Jobseeker: Download ATS-Compliant PDF Resume ----
@login_required
def download_ats_resume(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=user)
    
    career = getattr(profile, 'career', None)
    preferred_role = career.preferred_role if career and career.preferred_role else 'Software Developer'
    
    data = {
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'location': f"{profile.state}, {profile.country}" if profile.state else "India",
        'preferred_role': preferred_role,
        'technical_skills': list(profile.skills.filter(skill_type='technical').values_list('name', flat=True)),
        'soft_skills': list(profile.skills.filter(skill_type='soft').values_list('name', flat=True)),
        'projects': profile.projects.all(),
        'verified_badges': list(profile.verified_projects.filter(is_verified=True).values('badge_name', 'ai_score')),
        'educations': profile.educations.all(),
        'certifications': profile.certifications.all()
    }
    
    pdf = generate_ats_resume_pdf(data)
    clean_filename = re.sub(r'[^a-zA-Z0-9_]', '_', user.name)
    return FileResponse(pdf, as_attachment=False, filename=f"{clean_filename}_ATS_Resume.pdf")

# ---- Jobseeker: Project-Based Skill Verification ----
@login_required
def project_verify(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser,id=user_id)
    profile,_ = Profile.objects.get_or_create(user=user)
    result = None

    if request.method == 'POST':
        title = request.POST.get('title','').strip()
        domain = request.POST.get('domain','').strip()
        technology = request.POST.get('technology','').strip()
        repo_url = request.POST.get('repo_url','').strip()
        live_url = request.POST.get('live_url','').strip()
        arch_notes = request.POST.get('arch_notes','').strip()

        if not title or not technology:
            messages.error(request,'Project details are required.')
        else:
            result = evaluate_project_submission(
                title=title, domain=domain, technology=technology,
                repo_url=repo_url, live_url=live_url, arch_notes=arch_notes,
            )
            ProjectVerification.objects.create(
                profile=profile,title=title,domain=domain,
                technology=technology,repo_url=repo_url,
                live_url = live_url,arch_notes=arch_notes,
                ai_score=result['total_score'],
                badge_name=result['badge_name'], badge_level=result['badge_level'],
                is_verified=result['is_verified'],
                verified_at=(
                    timezone.now()
                    if result['is_verified'] else None
                )
            )
            if result['is_verified']:
                messages.success(request,'Skill Verification Complete')
            else:
                messages.warning(request,f'Skill Verified with {result['total_score']}%')    


    context = {'menu':stud_menu,'domain':domains.items(),'result':result}
    return render(request,'jobseeker/verification.html',context)

# ---- View Skill Badges ----
@login_required
def skillbadge(request):
    user_id=request.session.get('user_id')
    user = get_object_or_404(RoleUser,id=user_id)
    profile = get_object_or_404(Profile,user=user)
    verified = ProjectVerification.objects.filter(
        profile=profile, is_verified=True).order_by('-verified_at')
    context={'menu':stud_menu,'verified':verified} 
    return render(request,'jobseeker/skillbadge.html',context)

# ---- Jobseeker: Mock Interview ----
@login_required
def interview(request):
    context={"menu":stud_menu,"roles":role.items(),
             "types":interview_type,"experience":experience.items()}
    if request.method == 'POST':
        role_name = request.POST.get('role')
        interview_level = request.POST.get('type')
        experience_name = request.POST.get('experience')
        
        # ---- Selected Role ---- 
        role_display = next(
            name for name, value in role.items()
            if value == role_name
        )
        
        # ---- Generate Questions ----
        selected_questions = generate_questions(
            role=role_display, interview_type=interview_level,
            experience=experience_name
        )

        if not selected_questions:
            return render(
                request,
                "jobseeker/settings.html",
                {
                    **context,
                    "error": "Unable to generate interview questions."
                }
            )
        # ---- Store Interview Information ----
        request.session['role_name']=role_display
        request.session['interview_questions']=selected_questions
        request.session['current_question']=0
        request.session['interview_scores']=[]

        request.session['interview'] = {
            'type': interview_level,'experience': experience_name
        }  
        return redirect('session')
    return render(request,"jobseeker/settings.html",context)

@login_required
def session(request):
    questions = request.session.get('interview_questions',[])
    current_question = request.session.get('current_question',0)
    scores = request.session.get('interview_scores',[])

    if not questions:
        return redirect('interview')

    if request.method == 'POST':
        answer = request.POST.get('answer','')
        question_data = questions[current_question]
        result = evaluate_answer(answer, question_data) 

        result['question'] = question_data['question']
        scores.append(result)

        request.session['interview_scores']=scores
        current_question += 1
        request.session['current_question'] = current_question

        if current_question >= len(questions):
            overall_score = calculate_overall_score(
                [item['score'] for item in scores])
                
            request.session['overall_score'] = overall_score
            return JsonResponse({
                'completed': True,
                'redirect':'/jobseeker/interview/analysis/'
            })  

        question_data = questions[current_question]

        if isinstance(question_data, dict):
            question_text = question_data['question']
        else:
            question_text = question_data

        return JsonResponse({
            'completed':False,'question':question_text,
            'question_number': current_question + 1
        }) 

    question_data = questions[current_question]
    if isinstance(question_data, dict):
        question_text = question_data['question']
    else:
        question_text = question_data

    context={"menu":stud_menu,'role':role.items(),"question":question_text,
             "role_name": request.session.get('role_name'),
             "interview": request.session.get('interview'),
             "question_number":current_question+1,"total_questions":len(questions) 
            }
    return render(request,"jobseeker/interview.html",context)

@login_required
def analysis(request):
    scores = request.session.get('interview_scores',[])
    overall_score = request.session.get('overall_score',0)

    keyword_scores = [item.get('keyword_score',0) for item in scores]
    similarity_scores = [item.get('similarity_score',0) for item in scores]

    keyword_score = calculate_overall_score(keyword_scores)
    similarity_score = calculate_overall_score(similarity_scores)

    total_keywords=0; total_matched = 0

    for item in scores:
        total_matched += len(item.get('matched_keywords',[]))
        total_keywords += (
            len(item.get('matched_keywords',[])) +
            len(item.get('missing_keywords',[]))
        )

    if total_keywords:
        skill_coverage = round((total_matched / total_keywords) * 100)
    else:
        skill_coverage = 0    
    
    context={"menu":stud_menu,'role':role.items(),
        'question_results':scores, 'overall_score':overall_score,
        "keyword_score":keyword_score,"similarity_score":similarity_score,
        "skill_coverage":skill_coverage
    }
    return render(request,'jobseeker/analysis.html',context)

# ---- Recruiter: Dashboard ----
@login_required
def recruiter(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    
    active_jobs_count = JobPost.objects.filter(recruiter=user, status='Active').count()
    total_applications = JobApplication.objects.filter(job__recruiter=user).count()
    shortlisted_count = JobApplication.objects.filter(job__recruiter=user, status='shortlisted').count()
    total_candidates = RoleUser.objects.filter(role='jobseeker').count()
    
    recent_applications = JobApplication.objects.filter(job__recruiter=user).select_related('job', 'candidate', 'candidate__profile').order_by('-applied_at')[:6]
    
    # Skill Match Distribution
    top_skills = Skill.objects.filter(skill_type='technical').values('name').annotate(cnt=models.Count('name')).order_by('-cnt')[:5]
    skill_match_data = {}
    for s in top_skills:
        skill_match_data[s['name']] = min(95, 60 + s['cnt'] * 8)
    if not skill_match_data:
        skill_match_data = ai_match
        
    context = {
        "menu": comp_menu,
        "active_jobs_count": active_jobs_count,
        "total_applications": total_applications,
        "shortlisted_count": shortlisted_count,
        "total_candidates": total_candidates,
        "recent_applications": recent_applications,
        "ai_match": skill_match_data,
        "user": user
    }
    return render(request, 'recruiter/recruiter.html', context)

# ---- Recruiter: Verified Skill Search ----
@login_required
def candidate(request):
    query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip()
    badge_filter = request.GET.get('verified_only', '').strip()
    
    candidates_qs = RoleUser.objects.filter(role='jobseeker').select_related('profile')
    if query:
        candidates_qs = candidates_qs.filter(
            models.Q(name__icontains=query) |
            models.Q(email__icontains=query) |
            models.Q(profile__skills__name__icontains=query)
        ).distinct()
        
    candidate_cards = []
    for c in candidates_qs:
        prof = getattr(c, 'profile', None)
        if not prof:
            continue
        c_skills = list(prof.skills.filter(skill_type='technical').values_list('name', flat=True))
        v_badges = list(prof.verified_projects.filter(is_verified=True).values('badge_name', 'ai_score', 'badge_level'))
        
        if badge_filter == 'yes' and not v_badges:
            continue
            
        career = getattr(prof, 'career', None)
        cand_role = career.preferred_role if career and career.preferred_role else "Software Developer"
        if role_filter and role_filter.lower() not in cand_role.lower():
            continue
            
        edu = prof.educations.first()
        qual = f"{edu.degree} in {edu.course}" if edu else "Graduate"
        
        candidate_cards.append({
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'phone': c.phone,
            'role': cand_role,
            'qualification': qual,
            'skills': c_skills[:6],
            'verified_badges': v_badges,
            'verified_count': len(v_badges),
            'projects_count': prof.projects.count(),
            'location': f"{prof.state}, {prof.country}" if prof.state else "India"
        })
        
    context = {
        "menu": comp_menu,
        "roles": role,
        "candidates": candidate_cards,
        "query": query,
        "role_filter": role_filter,
        "badge_filter": badge_filter
    }
    return render(request, 'recruiter/candidate.html', context)

# ---- Recruiter: Candidate Detail AJAX/Modal ----
@login_required
def candidate_detail(request, user_id):
    candidate_user = get_object_or_404(RoleUser, id=user_id, role='jobseeker')
    profile, _ = Profile.objects.get_or_create(user=candidate_user)
    data = {
        'id': candidate_user.id,
        'name': candidate_user.name,
        'email': candidate_user.email,
        'phone': candidate_user.phone,
        'location': f"{profile.state}, {profile.country}" if profile.state else "",
        'role': profile.career.preferred_role if hasattr(profile, 'career') else 'Software Developer',
        'skills': list(profile.skills.values('name', 'skill_type')),
        'educations': list(profile.educations.values('degree', 'course', 'institution', 'cgpa', 'passing_year')),
        'projects': list(profile.projects.values('title', 'domain', 'technology')),
        'verified_badges': list(profile.verified_projects.filter(is_verified=True).values('title', 'badge_name', 'ai_score', 'badge_level', 'repo_url', 'live_demo_url')),
        'certifications': list(profile.certifications.values('name', 'organization', 'issue_date'))
    }
    return JsonResponse(data)

# ---- Recruiter: Post New Job ----
@login_required
def postJob(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    
    if request.method == 'POST':
        title = request.POST.get('job', '').strip()
        location_name = request.POST.get('location', '').strip()
        work_mode = request.POST.get('work_mode', 'Onsite').strip()
        experience_val = request.POST.get('experience', 'Fresher').strip()
        qualification = request.POST.get('qualification', '').strip()
        openings = request.POST.get('count', '1').strip()
        skills_list = request.POST.getlist('skills')
        deadline = request.POST.get('deadline') or None
        description = request.POST.get('description', '').strip()
        salary_range = request.POST.get('salary_range', '').strip()
        
        if not title:
            messages.error(request, "Job Title is required.")
        else:
            JobPost.objects.create(
                recruiter=user,
                title=title,
                company_name=user.name,
                location=location_name or "Remote",
                work_mode=work_mode,
                experience=experience_val,
                qualification=qualification,
                openings=int(openings) if openings.isdigit() else 1,
                required_skills=", ".join(skills_list),
                deadline=deadline,
                description=description or f"We are seeking an innovative {title} to join our growing engineering team.",
                salary_range=salary_range,
                status='Active'
            )
            messages.success(request, f"Job Posting '{title}' created successfully!")
            return redirect('listing')
            
    context = {
        "menu": comp_menu,
        "work": work,
        "experience": experience.items(),
        "skills": tskills
    }
    return render(request, 'recruiter/job.html', context)

# ---- Recruiter: Job Listings Management ----
@login_required
def listing(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    
    query = request.GET.get('search', '').strip()
    mode_filter = request.GET.get('mode', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    jobs_qs = JobPost.objects.filter(recruiter=user).annotate(app_count=models.Count('applications')).order_by('-created_at')
    if query:
        jobs_qs = jobs_qs.filter(models.Q(title__icontains=query) | models.Q(location__icontains=query))
    if mode_filter:
        jobs_qs = jobs_qs.filter(work_mode__iexact=mode_filter)
    if status_filter:
        jobs_qs = jobs_qs.filter(status__iexact=status_filter)
        
    context = {
        "menu": comp_menu,
        "work": work,
        "jobs": jobs_qs,
        "query": query,
        "mode_filter": mode_filter,
        "status_filter": status_filter
    }
    return render(request, 'recruiter/listing.html', context)

# ---- Recruiter: Toggle Job Active/Closed ----
@login_required
def toggle_job_status(request, job_id):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    job = get_object_or_404(JobPost, id=job_id, recruiter=user)
    job.status = 'Closed' if job.status == 'Active' else 'Active'
    job.save()
    messages.success(request, f"Job '{job.title}' marked as {job.status}.")
    return redirect('listing')

# ---- Recruiter: Delete Job ----
@login_required
def delete_job(request, job_id):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    job = get_object_or_404(JobPost, id=job_id, recruiter=user)
    job_title = job.title
    job.delete()
    messages.success(request, f"Job '{job_title}' deleted.")
    return redirect('listing')

# ---- Recruiter: Automated AI Screening ----
@login_required
def screening(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    
    recruiter_jobs = JobPost.objects.filter(recruiter=user).order_by('-created_at')
    selected_job_id = request.GET.get('job_id')
    min_score = int(request.GET.get('min_score', 0))
    
    selected_job = None
    if selected_job_id and selected_job_id.isdigit():
        selected_job = recruiter_jobs.filter(id=int(selected_job_id)).first()
    if not selected_job:
        selected_job = recruiter_jobs.first()
        
    ranked_candidates = []
    if selected_job:
        apps = JobApplication.objects.filter(job=selected_job).select_related('candidate', 'candidate__profile')
        applied_user_ids = []
        for app in apps:
            applied_user_ids.append(app.candidate.id)
            prof = getattr(app.candidate, 'profile', None)
            v_badges = prof.verified_projects.filter(is_verified=True).count() if prof else 0
            ranked_candidates.append({
                'application_id': app.id,
                'candidate_id': app.candidate.id,
                'name': app.candidate.name,
                'email': app.candidate.email,
                'ai_score': app.ai_suitability_score,
                'matched_skills': app.matched_skills_list,
                'missing_skills': app.missing_skills_list,
                'status': app.status,
                'status_display': app.get_status_display(),
                'verified_badges': v_badges,
                'applied': True,
                'applied_at': app.applied_at
            })
            
        # Also screen registered jobseekers in the talent pool
        other_jobseekers = RoleUser.objects.filter(role='jobseeker').exclude(id__in=applied_user_ids)
        for c in other_jobseekers:
            prof = getattr(c, 'profile', None)
            if prof:
                suitability = calculate_ai_suitability(prof, selected_job)
                ranked_candidates.append({
                    'application_id': None,
                    'candidate_id': c.id,
                    'name': c.name,
                    'email': c.email,
                    'ai_score': suitability['score'],
                    'matched_skills': suitability['matched_skills'],
                    'missing_skills': suitability['missing_skills'],
                    'status': 'pool',
                    'status_display': 'Talent Pool',
                    'verified_badges': suitability['verified_badges_count'],
                    'applied': False,
                    'applied_at': None
                })
                
        if min_score > 0:
            ranked_candidates = [c for c in ranked_candidates if c['ai_score'] >= min_score]
        ranked_candidates.sort(key=lambda x: x['ai_score'], reverse=True)
        
    context = {
        "menu": comp_menu,
        "jobs": recruiter_jobs,
        "selected_job": selected_job,
        "candidates": ranked_candidates,
        "min_score": min_score
    }
    return render(request, 'recruiter/screening.html', context)

# ---- Recruiter: Applications Pipeline ----
@login_required
def applications(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    
    job_id = request.GET.get('job_id')
    status_filter = request.GET.get('status')
    
    recruiter_jobs = JobPost.objects.filter(recruiter=user)
    apps_qs = JobApplication.objects.filter(job__recruiter=user).select_related('job', 'candidate', 'candidate__profile').order_by('-applied_at')
    
    if job_id and job_id.isdigit():
        apps_qs = apps_qs.filter(job_id=int(job_id))
    if status_filter:
        apps_qs = apps_qs.filter(status=status_filter)
        
    context = {
        "menu": comp_menu,
        "jobs": recruiter_jobs,
        "applications": apps_qs,
        "selected_job_id": int(job_id) if job_id and job_id.isdigit() else None,
        "status_filter": status_filter
    }
    return render(request, 'recruiter/applications.html', context)

# ---- Recruiter: Update Application Status ----
@login_required
def update_app_status(request, app_id):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    app = get_object_or_404(JobApplication, id=app_id, job__recruiter=user)
    new_status = request.POST.get('status') or request.GET.get('status')
    if new_status in dict(JobApplication.STATUS_CHOICES):
        app.status = new_status
        app.save()
        messages.success(request, f"Updated application status for {app.candidate.name} to '{app.get_status_display()}'.")
    return redirect(request.META.get('HTTP_REFERER', 'applications'))

# ---- Recruiter: Interviews & Outreach ----
@login_required
def interviews(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(RoleUser, id=user_id)
    
    interviews_list = InterviewSchedule.objects.filter(recruiter=user).select_related('candidate', 'application', 'application__job').order_by('-scheduled_date', '-scheduled_time')
    recruiter_jobs = JobPost.objects.filter(recruiter=user)
    candidates = RoleUser.objects.filter(role='jobseeker')
    
    context = {
        "menu": comp_menu,
        "interviews": interviews_list,
        "jobs": recruiter_jobs,
        "candidates": candidates
    }
    return render(request, 'recruiter/interviews.html', context)

# ---- Recruiter: Schedule Interview ----
@login_required
def schedule_interview(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user = get_object_or_404(RoleUser, id=user_id)
        
        candidate_id = request.POST.get('candidate_id')
        app_id = request.POST.get('application_id')
        interview_type = request.POST.get('interview_type', 'technical')
        scheduled_date = request.POST.get('scheduled_date')
        scheduled_time = request.POST.get('scheduled_time')
        meeting_link = request.POST.get('meeting_link', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        candidate = get_object_or_404(RoleUser, id=candidate_id)
        application = JobApplication.objects.filter(id=app_id).first() if app_id else None
        
        InterviewSchedule.objects.create(
            application=application,
            recruiter=user,
            candidate=candidate,
            interview_type=interview_type,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            meeting_link=meeting_link or "https://meet.google.com/nov-skil-ai",
            notes=notes or "Technical interview focusing on core architectures and verified project implementations.",
            status='scheduled'
        )
        
        if application:
            application.status = 'interview_scheduled'
            application.save()
            
        messages.success(request, f"Interview scheduled with {candidate.name} on {scheduled_date} at {scheduled_time}!")
        return redirect('interviews')
    return render(request,'recruiter/interviews.html')

# Admin User
@login_required
def admin(request):
    context={'menu':admin_menu,'recent':recent_activity}
    return render(request, 'admin/admin.html', context)