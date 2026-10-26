from django.db import models

# Role User.
class RoleUser(models.Model):
    ROLE_CHOICES=[
        ('jobseeker','Jobseeker'),('recruiter','Recruiter'),
        ('faculty','Faculty'),('mentor','Mentor'),('admin','Admin')
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

# Profile
class Profile(models.Model):
    user = models.OneToOneField(RoleUser,on_delete=models.CASCADE,
            related_name='profile') 
    state = models.CharField(max_length=100,blank=True)
    country = models.CharField(max_length=100,blank=True)
    profile_image = models.ImageField(upload_to="profile/",
            blank=True,null=True)
    def __str__(self):
        return self.user.name

# Education
class Education(models.Model):
    profile = models.ForeignKey(Profile,on_delete=models.CASCADE,
            related_name="educations")
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    cgpa = models.DecimalField(max_digits=4,decimal_places=2,
            null=True,blank=True)
    percentage = models.DecimalField(max_digits=5,decimal_places=2,
            null=True,blank=True)
    passing_year = models.PositiveIntegerField(null=True,blank=True)
    def __str__(self):
        return f"{self.degree} - {self.course}"

# Locations
class Location(models.Model):
    name = models.CharField(max_length=100,unique=True)
    def __str__(self):
        return self.name 

# Career
class Career(models.Model):
    profile = models.OneToOneField(Profile,on_delete=models.CASCADE,
                related_name="career")
    preferred_role = models.CharField(max_length=100,blank=True)
    locations = models.ManyToManyField(Location,blank=True,
                related_name="career_profiles")
    work_mode = models.CharField(max_length=50,blank=True)
    expected_salary = models.DecimalField(max_digits=12,decimal_places=2,
            null=True,blank=True)
    def __str__(self):
        return f"{self.profile.user.name} Career"


# Skills
class Skill(models.Model):
    SKILL_TYPE = [("technical", "Technical"),("soft", "Soft"),]
    profile = models.ForeignKey(Profile,on_delete=models.CASCADE,
        related_name="skills")
    name = models.CharField(max_length=100)
    skill_type = models.CharField(max_length=20,choices=SKILL_TYPE)
    def __str__(self):
        return self.name

# Projects
class Project(models.Model):
    profile = models.ForeignKey(Profile,on_delete=models.CASCADE,
                related_name="projects")
    title = models.CharField(max_length=200)
    domain = models.CharField(max_length=100,blank=True)
    technology = models.TextField( blank=True)
    def __str__(self):
        return self.title 

# Certifications
class Certification(models.Model):
    profile = models.ForeignKey(Profile,on_delete=models.CASCADE,
                related_name="certifications")
    name = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)
    issue_date = models.CharField(max_length=7,blank=True)
    def __str__(self):
        return self.name

# Job Posting (Recruiter)
class JobPost(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Closed', 'Closed')]
    recruiter = models.ForeignKey(RoleUser, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=150)
    work_mode = models.CharField(max_length=50, default='Onsite')
    job_type = models.CharField(max_length=50, default='Full Time')
    experience = models.CharField(max_length=50, default='Fresher')
    qualification = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    required_skills = models.TextField(help_text="Comma-separated skills")
    salary_range = models.CharField(max_length=100, blank=True)
    openings = models.PositiveIntegerField(default=1)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"



# Job Application (Jobseeker -> Recruiter)
class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('scheduled', 'Interview'),
        ('rejected', 'Rejected'),
        ('selected', 'Selected')
    ]
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(RoleUser, on_delete=models.CASCADE, related_name='job_applications')
    cover_note = models.TextField(blank=True)
    ai_suitability_score = models.PositiveIntegerField(default=0)
    matched_skills = models.TextField(blank=True)
    missing_skills = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'candidate')

    def __str__(self):
        return f"{self.candidate.name} - {self.job.title}"

    @property
    def matched_skills_list(self):
        if not self.matched_skills:
            return []
        return [s.strip() for s in self.matched_skills.split(',') if s.strip()]

    @property
    def missing_skills_list(self):
        if not self.missing_skills:
            return []
        return [s.strip() for s in self.missing_skills.split(',') if s.strip()]


# Project-Based Skill Verification & Badges (SkillNova AI Core Feature)
class ProjectVerification(models.Model):
    DOMAIN_CHOICES = [
        ('frontend','Frontend Development'),
        ('backend','Backend Development'),
        ('fullstack','Full-Stack Development'),
        ('data','Data Analytics & NLP'),
        ('iot','IoT Development')
    ]
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='verified_projects')
    title = models.CharField(max_length=200)
    domain = models.CharField(max_length=100, blank=True, choices=DOMAIN_CHOICES)
    technology = models.TextField(blank=True)
    repo_url = models.URLField(max_length=300, blank=True)
    live_url = models.URLField(max_length=300, blank=True)
    arch_notes = models.TextField(blank=True)
    ai_score = models.PositiveIntegerField(default=0)
    badge_name = models.CharField(max_length=150, blank=True)
    badge_level = models.CharField(max_length=50, default='Verified Developer')
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.user.name} - {self.title} ({self.badge_name})"


# Recruiter Direct Outreach & Interview Scheduling
class InterviewSchedule(models.Model):
    TYPE_CHOICES = [
        ('technical', 'Technical Level'),
        ('hr', 'HR Level'),
        ('managerial', 'Managerial Level')
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews', null=True, blank=True)
    recruiter = models.ForeignKey(RoleUser, on_delete=models.CASCADE, related_name='scheduled_interviews')
    candidate = models.ForeignKey(RoleUser, on_delete=models.CASCADE, related_name='candidate_interviews')
    interview_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='technical')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    meeting_link = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview with {self.candidate.name} for {self.application.job.title if self.application else 'Role'}"

     

