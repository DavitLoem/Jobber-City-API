from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os

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

# បន្ថែម CORS Middleware សម្រាប់អនុញ្ញាតឱ្យ Admin Web អាចហៅ API នេះបាន
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # ពេលដាក់ Production គួរដូរជា Domain របស់ Admin Web (ឧ. ["https://admin.jobbercity.com"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
from src.core.mongo import categories_collection
from src.domains.auth.router.auth_router import router as auth_router
from src.domains.auth.router.admin_auth_router import router as admin_auth_router
from src.domains.category.routes.category_route import router as category_router
from src.domains.category.routes.admin_category_route import router as admin_category_router


app.include_router(admin_auth_router)
app.include_router(admin_category_router)
app.include_router(auth_router) # បន្ថែម Router សម្រាប់ Authentication (Login/Logout) របស់ Admin
app.include_router(category_router)

