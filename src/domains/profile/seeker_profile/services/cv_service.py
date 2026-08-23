import io
import os
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.core.mongo import (
    seeker_profiles_collection,
    users_collection,
    categories_collection,
    provinces_collection,
    districts_collection,
)
from src.utils.cloudinary import upload_document

# 🎯 Path ទៅកាន់ Folder ដែលផ្ទុក Template CV ទាំងអស់ (src/templates/cv/*.html)
_TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
    "templates", "cv",
)

# 🎯 កន្លែងចុះឈ្មោះ Template ថ្មីៗ — បន្ថែម Template ថ្មីគ្រាន់តែបន្ថែម Row មួយទីនេះ
# ព្រមទាំងបង្កើត File HTML ដូចគ្នាឈ្មោះនៅក្នុង src/templates/cv/
CV_TEMPLATES: dict[str, dict] = {
    "modern": {
        "name": "Modern",
        "description": "Two-column layout with a dark sidebar for contact info, skills and languages — clean and contemporary.",
        "file": "modern.html",
    },
    "classic": {
        "name": "Classic",
        "description": "Traditional single-column resume, ATS-friendly and easy for recruiters and applicant-tracking systems to scan.",
        "file": "classic.html",
    },
    "elegant": {
        "name": "Elegant",
        "description": "Bold gradient header with soft purple accents — a polished, professional look that stands out.",
        "file": "elegant.html",
    },
}

_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


class CVService:

    def list_templates(self) -> list[dict]:
        return [
            {"id": key, "name": val["name"], "description": val["description"]}
            for key, val in CV_TEMPLATES.items()
        ]

    def _validate_template(self, template_id: str) -> dict:
        template = CV_TEMPLATES.get(template_id)
        if not template:
            allowed = ", ".join(CV_TEMPLATES.keys())
            raise HTTPException(status_code=400, detail=f"Unknown template '{template_id}'. Allowed values: {allowed}.")
        return template

    def _format_date(self, value) -> Optional[str]:
        """បំប្លែង Datetime ទៅជា Format ស្អាតៗសម្រាប់បង្ហាញលើ CV (ឧ. 'Jan 2023')"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value.strftime("%b %Y")
        return str(value)

    async def _build_context(self, user_id: str) -> dict:
        """ប្រមូលទិន្នន័យទាំងអស់ពី Collections ផ្សេងៗគ្នា ហើយរៀបចំវាឱ្យស្រេចរួចរាល់សម្រាប់ដាក់ចូល Template"""
        user_oid = ObjectId(user_id)

        user = await users_collection.find_one({"_id": user_oid})
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        profile = await seeker_profiles_collection.find_one({"user_id": user_oid})
        if not profile:
            raise HTTPException(
                status_code=400,
                detail="Please complete your profile (personal info, experience, education) before generating a CV.",
            )

        # ១. ដោះស្រាយឈ្មោះខេត្ត/ស្រុក ពី ObjectId ទៅជាអក្សរ
        province_name = None
        district_name = None
        if profile.get("province_id"):
            province = await provinces_collection.find_one({"_id": profile["province_id"]})
            if province:
                province_name = province.get("name_en") or province.get("name_km")
        if profile.get("district_id"):
            district = await districts_collection.find_one({"_id": profile["district_id"]})
            if district:
                district_name = district.get("name_en") or district.get("name_km")
        location = ", ".join([p for p in [district_name, province_name] if p]) or None

        # ២. ដោះស្រាយឈ្មោះជំនាញឯកទេស (Expertise Categories)
        category_names = []
        category_ids = profile.get("expertise_category_ids") or []
        if category_ids:
            cursor = categories_collection.find({"_id": {"$in": category_ids}})
            async for cat in cursor:
                if cat.get("name"):
                    category_names.append(cat["name"])

        # ៣. តម្រៀប Experience/Education តាមកាលបរិច្ឆេទចុងក្រោយបំផុតមុន ព្រមទាំង Format កាលបរិច្ឆេទ
        def sort_key(item: dict):
            return item.get("start_date") or datetime.min.replace(tzinfo=timezone.utc)

        experiences = sorted(profile.get("experiences") or [], key=sort_key, reverse=True)
        for exp in experiences:
            exp["start_date_display"] = self._format_date(exp.get("start_date"))
            exp["end_date_display"] = "Present" if exp.get("is_current_job") else self._format_date(exp.get("end_date"))

        educations = sorted(profile.get("educations") or [], key=sort_key, reverse=True)
        for edu in educations:
            edu["start_date_display"] = self._format_date(edu.get("start_date"))
            edu["end_date_display"] = self._format_date(edu.get("end_date")) or "Present"

        trainings = sorted(profile.get("trainings") or [], key=sort_key, reverse=True)
        for t in trainings:
            t["start_date_display"] = self._format_date(t.get("start_date"))
            t["end_date_display"] = self._format_date(t.get("end_date"))

        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "Your Name"

        return {
            "full_name": full_name,
            "current_position": profile.get("current_position"),
            "email": user.get("email"),
            "phone_number": profile.get("phone_number"),
            "location": location,
            # 🎯 ចំណាំ៖ Field ពិតប្រាកដនៅក្នុង Database គឺ profile_image_url (មិនមែន image_url ដូចក្នុង Model ទេ)
            # ព្រោះ attachment_service.py សរសេរចូល Field នេះជាក់ស្តែង
            "photo_url": profile.get("profile_image_url"),
            "biography": profile.get("biography"),
            "linkedin_url": profile.get("linkedin_url"),
            "portfolio_url": profile.get("portfolio_url"),
            "date_of_birth": self._format_date(profile.get("date_of_birth")),
            "gender": profile.get("gender"),
            "marital_status": profile.get("marital_status"),
            "nationality": profile.get("nationality"),
            "skills": profile.get("skills") or [],
            "expertise_categories": category_names,
            "experiences": experiences,
            "educations": educations,
            "trainings": trainings,
            "languages": profile.get("languages") or [],
        }

    async def preview_html(self, user_id: str, template_id: str) -> str:
        """ត្រឡប់ HTML ដើម្បីមើលមុន (Preview) - លឿនជាង PDF ព្រោះមិនចាំបាច់ Render+Upload"""
        template_info = self._validate_template(template_id)
        context = await self._build_context(user_id)
        template = _jinja_env.get_template(template_info["file"])
        return template.render(**context)

    async def generate_pdf(self, user_id: str, template_id: str) -> dict:
        """Render Template ➔ បំប្លែងទៅជា PDF ➔ Upload ទៅ Cloudinary ➔ រក្សាទុក URL ចូល Profile"""
        html_content = await self.preview_html(user_id, template_id)

        # 🎯 Import នៅទីនេះ (មិនមែននៅ Top of File ទេ) ដើម្បីកុំឱ្យ App Crash ពេល Startup
        # ប្រសិនបើ System Libraries របស់ WeasyPrint (Pango/Cairo) មិនទាន់បាន Install
        # (មើល notes/cv_generation_guide.md សម្រាប់ការណែនាំ Install)
        from weasyprint import HTML

        try:
            pdf_bytes = HTML(string=html_content, base_url=_TEMPLATE_DIR).write_pdf()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to render CV PDF: {e}")

        pdf_file = io.BytesIO(pdf_bytes)

        upload_result = upload_document(pdf_file, folder="jobber_city/cvs")
        if not upload_result.get("success"):
            raise HTTPException(
                status_code=502, detail=f"Failed to upload generated CV: {upload_result.get('message')}"
            )

        cv_url = upload_result["url"]
        now = datetime.now(timezone.utc)

        await seeker_profiles_collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": {
                "cv_url": cv_url,
                "cv_template_id": template_id,
                "cv_generated_at": now,
                # 🎯 Apply flow (bottom_apply_bar.dart), application-submission
                # service (seeker_application_service.py) and profile-completion
                # score all check "resume_url" — not "cv_url". Without setting
                # this too, a generated CV never satisfies "hasCv" and the
                # Apply button stays disabled with "No Resume/CV Found".
                "resume_url": cv_url,
                "updated_at": now,
            }},
        )

        return {"cv_url": cv_url, "template_id": template_id, "generated_at": now}

    async def get_current_cv(self, user_id: str) -> Optional[dict]:
        profile = await seeker_profiles_collection.find_one({"user_id": ObjectId(user_id)})
        if not profile or not profile.get("cv_url"):
            return {"cv_url": None, "template_id": None, "generated_at": None}
        return {
            "cv_url": profile.get("cv_url"),
            "template_id": profile.get("cv_template_id"),
            "generated_at": profile.get("cv_generated_at"),
        }


cv_service = CVService()
