from fastapi import APIRouter, Depends, Path, Query
from typing import List

from src.core.response import APIResponse
from src.dependencies.dependencies import require_employer # 🎯 ទាមទារសិទ្ធិ Employer
from src.domains.employer.applicant.services.applicant_service import ApplicantService
from src.domains.employer.applicant.schemas.job_application_schema import ApplicantStatusSummaryResponse, BulkUpdateApplicationStatus, UpdateApplicationStatus, ApplicantResponse

applicant_service = ApplicantService()

router = APIRouter(
    prefix="/api/employer/jobs", 
    tags=["Employer - Applicant Management"]
)

@router.get("/{job_id}/applicants", response_model=APIResponse[List[ApplicantResponse]])
async def get_job_applicants_route(
    job_id: str = Path(..., description="ID នៃការងារដែល Employer បានផុស"),
    status: str = Query("all", description="ត្រងតាម Status: pending, reviewed, shortlisted, interview, hired, rejected"),
    search: str = Query(None, description="ពាក្យគន្លឹះសម្រាប់ស្វែងរក"), 
    
    # 🟢 ១. បន្ថែម Query Parameter សម្រាប់ Sorting
    sort_by: str = Query("newest", description="ការតម្រៀប: newest, name_asc, interview_asc"),
    is_export: bool = Query(False, description="បន្ថែម Query Parameter សម្រាប់ Export"),
    
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_employer)
):
    user_id = str(current_user["_id"])
    result = await applicant_service.get_applicants_by_job(
        employer_user_id=user_id,
        job_id=job_id,
        status_filter=status,
        search_keyword=search,
        sort_by=sort_by,
        page=page,    
        limit=limit,
        is_export=is_export
    )
    
    return APIResponse(success=True, message="Get applicants successfully", data=result)
    
@router.get("/applications/dropdown", response_model=APIResponse)
async def get_job_filter_dropdown_route(
    current_user: dict = Depends(require_employer)
):
    """
    ទាញយកបញ្ជីការងាររបស់ក្រុមហ៊ុន សម្រាប់ប្រើប្រាស់ក្នុង Dropdown Filter លើទំព័រ Candidates
    """
    user_id = str(current_user["_id"])
    
    result = await applicant_service.get_employer_job_dropdown_list(
        employer_user_id=user_id
    )
    
    return APIResponse(
        success=True, 
        message="Job dropdown list fetched successfully", 
        data=result
    )
    
@router.get("/{job_id}/applicants/summary", response_model=APIResponse[ApplicantStatusSummaryResponse])
async def get_applicant_status_summary_route(
    job_id: str = Path(..., description="ID នៃការងារ (ដាក់ 'all' សម្រាប់ទាំងអស់)"),
    current_user: dict = Depends(require_employer)
):
    """ទាញយកចំនួនសរុបនៃបេក្ខជនក្នុង Status នីមួយៗ សម្រាប់ដាក់បង្ហាញលើ Tab របស់ Flutter"""
    
    user_id = str(current_user["_id"])
    result = await applicant_service.get_applicant_status_summary(
        employer_user_id=user_id,
        job_id=job_id
    )
    
    return APIResponse(
        success=True, 
        message="Get applicant summary successfully", 
        data=result
    )

@router.patch("/applications/{application_id}/status", response_model=APIResponse)
async def update_application_status_route(
    payload: UpdateApplicationStatus,
    application_id: str = Path(..., description="ID របស់ទិន្នន័យដាក់ពាក្យ (Application ID)"),
    current_user: dict = Depends(require_employer)
):
    """ប្តូរ Workflow Status របស់អ្នកដាក់ពាក្យ (ឧ. ពី pending ទៅ reviewed)"""
    
    user_id = str(current_user["_id"])
    result = await applicant_service.update_applicant_status(
        employer_user_id=user_id,
        application_id=application_id,
        new_status=payload.status,
        
        # 🟢 បន្ថែម ២ បន្ទាត់នេះ ដើម្បីឱ្យទិន្នន័យឆ្លងកាត់ទៅដល់ Service 
        interview_schedule=payload.interview_schedule,
        feedback=payload.feedback
    )
    
    return APIResponse(
        success=True, 
        message=f"Application status updated to {payload.status}", 
        data=result
    )

@router.patch("/applications/bulk-status", response_model=APIResponse)
async def bulk_update_application_status_route(
    payload: BulkUpdateApplicationStatus,
    current_user: dict = Depends(require_employer)
):
    """ប្តូរ Workflow Status របស់អ្នកដាក់ពាក្យច្រើននាក់ក្នុងពេលតែមួយ (Bulk Action)"""
    
    user_id = str(current_user["_id"])
    result = await applicant_service.bulk_update_applicant_status(
        employer_user_id=user_id,
        application_ids=payload.application_ids,
        new_status=payload.status,
        interview_schedule=payload.interview_schedule,
        feedback=payload.feedback
    )
    
    return APIResponse(
        success=True, 
        message=f"Successfully updated {result['modified_count']} applications to {payload.status}", 
        data=result
    )

@router.get("/seekers/{seeker_user_id}/profile", response_model=APIResponse)
async def view_seeker_profile_route(
    seeker_user_id: str = Path(..., description="ID របស់គណនី Seeker"),
    current_user: dict = Depends(require_employer)
):
    """Employer ចុចមើល Profile ពេញលេញរបស់ Seeker (ទម្រង់ Read Only)"""
    
    user_id = str(current_user["_id"])
    result = await applicant_service.get_seeker_profile_readonly(
        employer_user_id=user_id,
        seeker_user_id=seeker_user_id
    )
    
    return APIResponse(
        success=True, 
        message="Get seeker profile successfully", 
        data=result
    )