from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os
import time


load_dotenv()
# ទាញយក Environment (ឧ. local, staging, production)
app_env = os.getenv("APP_ENV", "local") # ដាក់ "local" ជា Default បើអត់មាន
show_docs = app_env in ["local", "staging"]

app = FastAPI(
    title="Jobber City API",
    description="API for Job Seeker and Employer Mobile App & Admin Dashboard",
    docs_url="/docs" if show_docs else None,
    redoc_url="/redoc" if show_docs else None,
    swagger_ui_parameters={"docExpansion": "none"}
)

# កំណត់ថាអ្នកណាខ្លះ (Domain ណាខ្លះ) អាចហៅ API នេះបាន
origins = [
    "http://localhost:3000",      # សម្រាប់ React/Next.js
    "http://localhost:8080",      # សម្រាប់ Vue
    "http://localhost:5000",      # សម្រាប់ Flutter Web
    # "https://www.jobbercity.com" # ដាក់ Domain ពិតប្រាកដរបស់អ្នកនៅពេល Deploy
    "*"                           # ឬដាក់ "*" ដើម្បីអនុញ្ញាតឱ្យហៅពីគ្រប់កន្លែង (ល្អសម្រាប់ការធ្វើតេស្ត)
]

# បន្ថែម CORS Middleware សម្រាប់អនុញ្ញាតឱ្យ Admin Web អាចហៅ API នេះបាន
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # ពេលដាក់ Production គួរដូរជា Domain របស់ Admin Web (ឧ. ["https://admin.jobbercity.com"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#​  ២. Custom Middleware (វាស់រយៈពេលដំណើរការ API)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # បញ្ជូន Request ទៅកាន់ Route (Endpoint) ដើម្បីដំណើរការ
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # បន្ថែម Header ថ្មីឈ្មោះ 'X-Process-Time' ចូលក្នុង Response
    response.headers["X-Process-Time"] = str(process_time)
    
    # ស្រេចចិត្ត: អ្នកអាច print ចេញមកក្រៅដើម្បីងាយស្រួលមើលក្នុង Terminal
    print(f"[{request.method}] {request.url.path} - Process Time: {process_time:.4f} seconds")
    
    return response

# 🎯 បន្ថែម Custom Exception Handler នេះចូល
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    ចាប់យក Error ដែលកើតឡើងពេល User បញ្ចូលទិន្នន័យខុស Schema
    ហើយរៀបចំវាឱ្យស្អាត ព្រមទាំងលាក់ `input` ដើម្បីសុវត្ថិភាព។
    """
    errors = exc.errors()
    formatted_errors = []
    
    for error in errors:
        # យកតែឈ្មោះ Field ដែល Error (ឧ. "password", "email")
        field = error["loc"][-1] if len(error["loc"]) > 0 else "unknown_field"
        
        formatted_errors.append({
            "field": field,
            "message": error["msg"]
        })
        
    # បោះ Response ត្រឡប់ទៅវិញជាទម្រង់ស្អាត (Clean JSON)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Data validation error",
            "errors": formatted_errors
        }
    )

# Redirect root URL
@app.get("/", include_in_schema=False)
async def root():
    if show_docs:
        return RedirectResponse(url="/docs")
    return {"message": "Jobber City API is running securely."}


# ==========================================
# Routes 
# ==========================================
from src.domains.auth.router.auth_router import router as auth_router
from src.domains.auth.router.admin_auth_router import router as admin_auth_router
from src.domains.category.routes.category_route import router as category_router
from src.domains.category.routes.admin_category_route import router as admin_category_router
from src.domains.location.routes.admin_location_route import router as admin_location_router
from src.domains.location.routes.mobile_location_router import router as location_router
from src.domains.profile.seeker_profile.routes.core_profile_router import router as seeker_profile_router
from src.domains.profile.seeker_profile.routes.attachment_router import router as seeker_attachment_router
from src.domains.profile.seeker_profile.routes.experience_router import router as seeker_experience_router
from src.domains.profile.seeker_profile.routes.education_router import router as seeker_education_router
from src.domains.profile.seeker_profile.routes.training_router import router as seeker_training_router
from src.domains.profile.seeker_profile.routes.language_router import router as seeker_language_router
from src.domains.master_data.routes.job_level_router import router as admin_job_level_router
from src.domains.master_data.routes.education_level_router import router as admin_education_level_router
from src.domains.master_data.routes.skill_router import router as admin_skill_router
from src.domains.master_data.routes.employment_type_router import router as admin_employment_type_router
from src.domains.master_data.routes.work_type_router import router as admin_work_type_router
from src.domains.master_data.routes.industry_router import router as admin_industry_router
from src.domains.master_data.routes.public_master_data_router import router as public_master_data_router
from src.domains.profile.company_profile.routes.company_profile_router import router as company_profile_router
from src.domains.employer.job_post.routes.job_post_router import router as job_post_router
from src.domains.employer.applicant.routes.applicant_router import router as applicant_router
from src.domains.seeker.job_feed.routes.job_feed_router import router as job_feed_router
from src.domains.seeker.application.routes.seeker_application_router import router as seeker_application_router


# =========================
# Admin Routes
# =========================
app.include_router(admin_auth_router)
# Admin Master Data Routes
app.include_router(admin_category_router)
app.include_router(admin_location_router)
app.include_router(admin_job_level_router)
app.include_router(admin_education_level_router)
app.include_router(admin_skill_router)
app.include_router(admin_employment_type_router)
app.include_router(admin_work_type_router)
app.include_router(admin_industry_router)

# =========================
# Mobile App Routes
# =========================
app.include_router(auth_router)
app.include_router(category_router)
app.include_router(location_router)
app.include_router(public_master_data_router)

# Seeker Routes
app.include_router(seeker_profile_router)
app.include_router(seeker_attachment_router)
app.include_router(seeker_experience_router)
app.include_router(seeker_education_router)
app.include_router(seeker_training_router)
app.include_router(seeker_language_router)
app.include_router(job_feed_router)
app.include_router(seeker_application_router)

# Employer Routes (បន្ថែមនៅទីនេះពេលដែលបានបង្កើតរួចហើយ)
app.include_router(company_profile_router)
app.include_router(job_post_router)
app.include_router(applicant_router)


