# ------ Import Library ------
import pymupdf, re
import numpy as np 

from django.conf import settings
from llama_cpp import Llama

class ResumeParser:
    # --- AI Model ---
    _embedding_model = None

    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            cls._embedding_model = Llama(
                model_path=str(settings.MINILM_MODEL_PATH),
                embedding=True, verbose=False
            )
        return cls._embedding_model    

    TECHNICAL_SKILLS={
        'Python','Java','Javascript','Typescript','C','C++','C#',
        'HTML', 'CSS','Bootstrap','React','React Native','Django',
        'Flask','FastAPI','Node','Express','PHP','MySQL',
        'Postgresql','Mongodb','SQLite','Flutter',
        'Git','Github','Docker','AWS'
    }
    SOFT_SKILLS={
        'Communication','Leadership','Teamwork','Project Management',
        'Problem solving','Time management','Adaptability','Crictical Thinking'
    }
    DEGREES={'bachelor':"Bachelor's",'master':"Master's",
        'phd':'PhD','doctorate':'PhD'}
    COURSES={
        'bca':'BCA','Bachelor of Computer Applications':'BCA',
        'mca':'MCA','Master of Computer Applications':'MCA',
        'b.tech':'B.Tech','btech':'B.Tech','m.tech':'M.Tech','mtech':'M.Tech'
    }
    SECTION_NAMES={
        'skills':['skills','technical skills','technical expertise',
            'core skills','core competencies','key skills','professional skills'],
        
        'experience':['experience','work experience','professional experience','employment',
            'employment history','work history','professional background'],
        
        'projects':['projects','academic projects','personal projects',
            'professional projects','project experience'],
        
        'education':['education','academic','academic background',
            'academic qualifications','educational qualifications'],
        
        'certifications':['certifications','certificates',
            'professional certifications','courses & certifications'],

        'achievements':['achievements','awards','honors','accomplishments']
    }

    EXPERIENCE_DATE_PATTERN=(
        r'('
        r'(?:January|February|March|April|May|June|July|'
        r'August|September|October|November|December)'
        r'\s+\d{4}' r'|20\d{2}' r')'
        r'\s*[-–]\s*' r'(Present|'
        r'(?:January|February|March|April|May|June|July|'
        r'August|September|October|November|December)'
        r'\s+\d{4}' r'|20\d{2})'
    )

    # ------ Initialization ------
    def __init__(self,pdf_file):
        self.pdf_file=pdf_file
        self.text=""
        self.lines=[]

    # ------ Text Normalization ------
    def normalize_text(self,text):
        text = text.replace('\x88', '')
        return re.sub(r'\s+',' ',text).strip()    

    # ------ PDF Extraction ------
    def extract_pdf(self):
        document=pymupdf.open(
            stream = self.pdf_file.read(),
            filetype='pdf'
        )
        pages=[] 
        for page in document:
            text = page.get_text('text')
            if text:
                pages.append(text)
        document.close()
        self.text = '\n'.join(pages)
        self.lines=[
            self.normalize_text(line)
            for line in self.text.splitlines()
            if line.strip()
        ]

    # ------ Resume Parser ------
    def parse(self):
        self.extract_pdf()
        return{
            'profile':self.extract_profile(),
            'education':self.extract_education(),
            'skills':self.extract_skills(),
            'experience':self.extract_experience(),
            'projects':self.extract_projects(),
            'certificates':self.extract_certificates(),
            'achievements':self.extract_achievements(),
            'embedding': self.extract_embedding()
        } 
    
    # ------ Profile Section ------
    def extract_profile(self):
        return{
            'fullname':self.extract_name(),
            'email':self.extract_regex(r"[\w.+-]+@[\w.-]+\.\w+"),
            'contact':self.extract_regex(r"(?:\+?\d{1,3}[-.\s]?)?\d{5}[-.\s]?\d{5}"),
            'linkedin':self.extract_regex(
                r"(?:https?://)?(?:www\.)?"r"linkedin\.com/in/[\w-]+"
            ),
            'github':self.extract_regex(
                r"(?:https?://)?(?:www\.)?"r"github\.com/[\w-]+"
            )
        }

    # ------ Profile Name ------ 
    def extract_name(self):
        ignored={'resume','curriculum vitae','cv','profile'}

        for line in self.lines[:5]:
            if line.lower() not in ignored:
                return line

        return ''        

    # ------ Section Detection ------
    def get_section(self,section):
        aliases = [
            x.lower().strip()
            for x in self.SECTION_NAMES[section]
        ]
        start = None
        for index, line in enumerate(self.lines):
            if line.lower().strip() in aliases:
                start = index + 1
                break
        if start is None:
            return[]
        all_headers = {
            header.lower().strip()
            for values in self.SECTION_NAMES.values()
            for header in values
        }
        result = []
        
        for line in self.lines[start:]:
            if line.lower().strip() in all_headers:
                break
            result.append(line.strip())
        return result

    # Skill Section
    def extract_skills(self):
        lines = self.get_section('skills')
        text = ' '.join(lines)
        return{
            'technical':self.find_keywords(text,self.TECHNICAL_SKILLS),
            'soft':self.find_keywords(text,self.SOFT_SKILLS)
        }
    def find_keywords(self,text,keywords):
        result = []
        for keyword in keywords:
            if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)",text,re.I):
                result.append(keyword)
        return result

    # ------ Education Section ------
    def extract_education(self):
        lines = self.get_section('education') 
        if not lines:
            return {}
        text = ' '.join(lines)
        return{
            'institution':self.find_institution(lines),
            'degree':self.find_degree(text),
            'course':self.find_course(text),
            'cgpa':self.extract_value(r"(?:cgpa|gpa)\s*[:\-]?\s*([\d.]+)",text),
            'percentage':self.extract_value(r"([\d.]+)\s*%",text),
            'passing_year':self.find_pass_year(text)
        }
    
    # ------ Degree ------
    def find_degree(self,text):
        text = text.lower()

        if re.search(r'\bph\.?d\b|\bdoctorate\b',text):
            return self.DEGREES['phd']
        if re.search(r"\bbachelor\b", text):
            return self.DEGREES["bachelor"]
        if re.search(r"\bmaster\b", text):
            return self.DEGREES["master"]

        return ""
    
    # ------ Course ------ 
    def find_course(self,text):
        text = text.lower()
        for key,value in self.COURSES.items():
            if re.search(rf"\b{re.escape(key)}\b", text,re.I):
                return value
        return "" 
       
    # ------ Institution ------
    def find_institution(self, lines):
        for line in lines:
            if re.search(r"college|university|institute",line,re.I):
                return line
        return ""

    # ------ Passing Year ------
    def find_pass_year(self,text):
        years = re.findall(r"\b(?:19|20)\d{2}\b",text)
        return years[-1] if years else ""

    # ------ Experience Section ------
    def extract_experience(self):
        lines = self.get_section('experience')
        experiences = []
        current_experience = None
        
        for line in lines:
            if '|' in line:
                if current_experience:
                    experiences.append(current_experience)
                role, company = line.split('|',1)
                current_experience={
                    'role':re.sub(r'^\d+\.\s*','',role).strip(),
                    'company': company.strip(),
                    'start': '','end': ''
                }  
                continue

            date_match = re.search(self.EXPERIENCE_DATE_PATTERN,line,re.I)

            if date_match and current_experience:
                current_experience['start'] = date_match.group(1)
                current_experience['end'] = date_match.group(2)
                continue

        if current_experience:
            experiences.append(current_experience)

        return experiences      

    # ------ Project Heading Detection ------
    def detect_project_heading(self,line):
        patterns=[
            r'^\d+\.\s*(.*?)\s*\|\s*(.*?)\s*$',
            r'^(.*?)\s*\|\s*(.*?)\s*$',
            r'^project\s*:\s*(.*?)\s*$'
        ] 

        for pattern in patterns:
            match = re.match(pattern,line,re.I)

            if match:
                return match.groups()

        return None        

    # ------ Projects ------
    def extract_projects(self):
        lines = self.get_section('projects')
        projects = []
        current_project = None

        for line in lines: 
            heading = self.detect_project_heading(line) 
            if heading:
                if current_project:
                    projects.append(current_project)
                
                title = heading[0].strip()
                domain = ''
                duration = ''   

                if len(heading) > 1:
                    domain = heading[1].strip() 

                year_match = re.search(
                    r'\b((?:19|20)\d{2}\s*[–-]\s*(?:19|20)\d{2})\b',domain
                )

                if year_match:
                    duration = year_match.group(1).strip()

                    domain = re.sub(
                        r'\s*(?:19|20)\d{2}\s*[–-]\s*(?:19|20)\d{2}\s*',
                        '',domain    
                    ).strip()    

                current_project = {
                    'title': title, 'domain': domain, 'duration':duration,
                    'technology': '', 'description': ''
                }  
                continue

            if re.match(
                r'^\s*(?:19|20)\d{2}\s*[–-]\s*(?:19|20)\d{2}\s*$',
                line
            ):
                if current_project:
                    current_project['duration'] = line.strip()
                continue

            if line.lower().startswith(('tech stack:', 'technologies:')):
                if current_project:
                    current_project['technology'] = (line.split(':', 1)[1].strip())
                continue

            if current_project:
                if current_project['description']:
                    current_project['description'] += ' ' + line
                else:
                    current_project['description'] = line

        if current_project:
            projects.append(current_project)  

        return projects              
  
    # ------ Certificates ------
    def extract_certificates(self):
        current_certificate = None
        lines = self.get_section("certifications")
        certificates = []
        months={
            "january": "01","february": "02","march": "03",
            "april": "04","may": "05","june": "06",
            "july": "07","august": "08","september": "09",
            "october": "10","november": "11","december": "12"
        }
        for line in lines:
            line = line.strip()
            if re.match(r"^\d+\.", line):
                if current_certificate:
                   certificates.append(current_certificate)
                name = re.sub(r"^\d+\.\s*","",line)
                current_certificate={
                    'name':name,'organization':'','issue_date':''
                }
                continue
            if '|' in line and current_certificate:
                organization, date = line.split("|", 1)
                current_certificate["organization"] = (organization.strip())
                date_match = re.search( 
                    r"(January|February|March|April|May|June|"
                    r"July|August|September|October|November|December)"
                    r"\s+(\d{4})",date,re.I
                )
                if date_match:
                    month = months[date_match.group(1).lower()]
                    year=date_match.group(2)
                    current_certificate["issue_date"] = (f"{year}-{month}")
                continue
        if current_certificate:
            certificates.append(current_certificate)
        return certificates

    # ------ Achievements ------
    def extract_achievements(self):
        return self.get_section('achievements')

    # ------ Regex helpers ------
    def extract_regex(self,pattern):
        match = re.search(pattern,self.text,re.I)
        return(
            match.group(0)
            if match
            else ""
        )
    def extract_value(self,pattern,text):
        match = re.search(pattern,text,re.I)
        return (
            match.group(1)
            if match
            else ""
        )

    # ---- MiniLM NLP Embedding ----
    def extract_embedding(self):
        if not self.lines:
            return []

        model = self.get_embedding_model()
        resume_text = ' '.join(self.lines)

        # Generate Embedding
        embedding = model.embed(resume_text, normalize=True)

        embedding = np.asarray(
            embedding, dtype=np.float32
        ).flatten()

        return embedding.tolist() 