from django.urls import path
from . import views

urlpatterns=[
    path('layout/',views.layout,name="layout"),
    path('',views.home, name="home"),
    path('register/',views.register,name="register"),
    path('login/',views.login,name="login"),
    path("logout/", views.logout, name="logout"),

    # ------ Jobseeker ------
    path('jobseeker/',views.jobseeker,name="jobseeker"),
    path('jobseeker/profile/',views.profile,name="profile"),
    path('jobseeker/profile/save',views.save_profile,name='save_profile'),
    path('jobseeker/skillgap/',views.skill,name='skillgap'),
    path('jobseeker/roadmap/',views.roadmap,name="roadmap"),
    path('jobseeker/ats-resume/',views.ats_resume,name="ats_resume"),
    path('jobseeker/ats-resume/download/',views.download_ats_resume,name="download_ats_resume"),
    path('jobseeker/verify-skills/',views.project_verify,name="project_verify"),
    path('jobseeker/skill-badge/',views.skillbadge,name="skillbadge"),
    path('jobseeker/cover/',views.cover,name="cover"),
    path('jobseeker/jobs/',views.jobs,name="jobs"),
    path('jobseeker/jobs/apply/<int:job_id>/',views.apply_job,name="apply_job"),
    path('jobseeker/jobs/applications/',views.applied,name="applied"),
    path('jobseeker/jobs/invitations',views.invitations,name="invitations"),
    path('jobseeker/interview/',views.interview,name="interview"),
    path('jobseeker/interview/session/',views.session,name="session"),
    path('jobseeker/interview/analysis/',views.analysis,name="analysis"),

    # ------ Recruiter -------
    path('recruiter/',views.recruiter,name='recruiter'),
    path('recruiter/candidate/',views.candidate,name='candidate'),
    path('recruiter/candidate/<int:user_id>/',views.candidate_detail,name='candidate_detail'),
    path('recruiter/post-job/',views.postJob,name="postJob"),
    path('recruiter/job-list/',views.listing, name='listing'),
    path('recruiter/job-list/<int:job_id>/toggle/',views.toggle_job_status, name='toggle_job_status'),
    path('recruiter/job-list/<int:job_id>/delete/',views.delete_job, name='delete_job'),
    path('recruiter/screening/',views.screening,name='screening'),
    path('recruiter/applications/',views.applications,name='applications'),
    path('recruiter/applications/<int:app_id>/status/',views.update_app_status,name='update_app_status'),
    path('recruiter/interviews/',views.interviews,name='interviews'),
    path('recruiter/interviews/schedule/',views.schedule_interview,name='schedule_interview'),

    # ------ Admin ------
    path('skillnova/',views.admin,name="admin")
]