"""
Seeds the master-data collections that job posting depends on
(categories, job levels, education levels, employment types, work types,
skills). Safe to re-run — every insert checks for an existing item with the
same name (case-insensitive) first, so it never creates duplicates.

Run from the backend project root, with your venv active (so it picks up
the same MONGO_URL / MONGO_DB_NAME your API already uses from .env):

    cd Jobber-City-API
    source .venv/bin/activate
    python -m scripts.seed_master_data
"""

import asyncio
from datetime import datetime, timezone

from src.core.mongo import (
    categories_collection,
    job_levels_collection,
    education_levels_collection,
    employment_types_collection,
    work_types_collection,
    skills_collection,
)

# ==========================================
# Data to seed — edit/add to these lists freely, then re-run the script.
# ==========================================

CATEGORIES = [
    "Software Development",
    "Design",
    "Marketing",
    "Sales",
    "Customer Service",
    "Human Resources",
    "Finance & Accounting",
]

JOB_LEVELS = ["Entry Level", "Junior", "Mid Level", "Senior", "Manager"]

EDUCATION_LEVELS = [
    "High School",
    "Associate Degree",
    "Bachelor's Degree",
    "Master's Degree",
    "PhD",
]

EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]

WORK_TYPES = ["On-site", "Remote", "Hybrid"]

SKILLS = [
    "Python", "JavaScript", "Dart", "Flutter", "FastAPI", "React",
    "SQL", "MongoDB", "Communication", "Project Management",
]


async def seed_generic(collection, names: list[str]) -> None:
    """Shared shape for job_levels / education_levels / employment_types /
    work_types / skills — matches GenericMasterDataModel.to_create_dict()."""
    label = collection.name
    for order, name in enumerate(names, start=1):
        existing = await collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        if existing:
            print(f"  [skip] {label}: '{name}' already exists")
            continue
        now = datetime.now(timezone.utc)
        await collection.insert_one({
            "name": name,
            "order": order,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        print(f"  [+] {label}: '{name}' created")


async def seed_categories(names: list[str]) -> None:
    """Categories use their own model shape (icon_url, sort_order) —
    matches CategoryModel.to_create_dict()."""
    for order, name in enumerate(names, start=1):
        existing = await categories_collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        if existing:
            print(f"  [skip] categories: '{name}' already exists")
            continue
        now = datetime.now(timezone.utc)
        await categories_collection.insert_one({
            "name": name,
            "icon_url": None,
            "sort_order": order,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        print(f"  [+] categories: '{name}' created")


async def main():
    print("Seeding categories...")
    await seed_categories(CATEGORIES)

    print("Seeding job levels...")
    await seed_generic(job_levels_collection, JOB_LEVELS)

    print("Seeding education levels...")
    await seed_generic(education_levels_collection, EDUCATION_LEVELS)

    print("Seeding employment types...")
    await seed_generic(employment_types_collection, EMPLOYMENT_TYPES)

    print("Seeding work types...")
    await seed_generic(work_types_collection, WORK_TYPES)

    print("Seeding skills...")
    await seed_generic(skills_collection, SKILLS)

    print("\nDone. Re-run anytime — existing items are skipped, not duplicated.")


if __name__ == "__main__":
    asyncio.run(main())
