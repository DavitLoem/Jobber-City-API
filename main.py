from fastapi import FastAPI
from src.controllers.auth import router as auth_router
from src.controllers.employer import router as employer_router
from src.controllers.slider import router as slider_router
from src.controllers.cities import router as cities_router
from src.controllers.expertise import router as expertise_router
from src.controllers.fill_profile import router as fill_profile_router

app = FastAPI(
    title="Jobber City API",
    description="Jobber City API for job seekers and employers",
    version="1.0.0"
)



app.include_router(auth_router)
app.include_router(cities_router)
app.include_router(expertise_router)
app.include_router(fill_profile_router)
app.include_router(employer_router)
app.include_router(slider_router)
