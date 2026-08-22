from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from src.core.response import APIResponse
from src.dependencies.dependencies import get_current_user, require_seeker
from src.domains.profile.seeker_profile.schema.cv_schema import (
    CVTemplateInfo,
    GenerateCVRequest,
    GenerateCVResponse,
    CurrentCVResponse,
)
from src.domains.profile.seeker_profile.services.cv_service import cv_service

# 🎯 មុខងារនេះសម្រាប់ Seeker តែប៉ុណ្ណោះ (Employer មិនមាន CV ត្រូវបង្កើតទេ)
router = APIRouter(
    prefix="/api/seeker/cv",
    tags=["Seeker - CV Generator"],
    dependencies=[Depends(require_seeker)],
)


@router.get("/templates", response_model=APIResponse[List[CVTemplateInfo]])
async def list_cv_templates():
    """ទាញយកបញ្ជី Template CV ទាំងអស់ដែលអាចជ្រើសរើសបាន (សម្រាប់ឱ្យ App បង្ហាញ Template Picker)"""
    return APIResponse(success=True, message="CV templates fetched successfully", data=cv_service.list_templates())


@router.get("/preview/{template_id}", response_class=HTMLResponse)
async def preview_cv(template_id: str, current_user: dict = Depends(get_current_user)):
    """
    ត្រឡប់ HTML ឆៅដើម្បីមើលមុន (Preview) - Flutter អាចបង្ហាញវាក្នុង WebView ភ្លាមៗ
    លឿនជាង /generate ព្រោះមិនចាំបាច់ Render PDF ឬ Upload ទៅ Cloudinary ទេ
    """
    html_content = await cv_service.preview_html(str(current_user["_id"]), template_id)
    return HTMLResponse(content=html_content)


@router.post("/generate", response_model=APIResponse[GenerateCVResponse])
async def generate_cv(
    payload: GenerateCVRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    បង្កើត CV ជា PDF ពិតប្រាកដ តាម Template ដែលបានជ្រើសរើស, Upload ទៅ Cloudinary,
    ហើយរក្សាទុក Link ចូល Profile របស់ Seeker (cv_url) ដើម្បីប្រើប្រាស់ពេលក្រោយ
    (ឧ. ភ្ជាប់ជាមួយ Job Application)។
    """
    result = await cv_service.generate_pdf(str(current_user["_id"]), payload.template_id)
    return APIResponse(success=True, message="CV generated successfully", data=result)


@router.get("/current", response_model=APIResponse[CurrentCVResponse])
async def get_current_cv(current_user: dict = Depends(get_current_user)):
    """ទាញយក CV ចុងក្រោយបំផុតដែលធ្លាប់បង្កើត (បើមាន) - ប្រើសម្រាប់បង្ហាញលើ Profile Screen"""
    result = await cv_service.get_current_cv(str(current_user["_id"]))
    return APIResponse(success=True, message="Current CV fetched successfully", data=result)
