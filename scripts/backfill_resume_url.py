"""
One-time fix for CVs generated BEFORE cv_service.py was patched to also set
"resume_url" alongside "cv_url" on the seeker profile.

Symptom this fixes: seeker already tapped "Generate" on the CV Generator
screen (so seeker_profiles.cv_url is set), but the Apply modal still shows
"No Resume/CV Found" because it (and the application-submission backend)
checks "resume_url", which was never populated for CVs generated before the
fix.

What it does: for every seeker profile that has a "cv_url" but an empty/
missing "resume_url", copies cv_url -> resume_url.

Safe to re-run — only touches profiles where resume_url is still empty.

Run from the backend project root, with your venv active:

    cd Jobber-City-API
    source .venv/bin/activate
    python -m scripts.backfill_resume_url
"""

import asyncio

from src.core.mongo import seeker_profiles_collection


async def main():
    cursor = seeker_profiles_collection.find({
        "cv_url": {"$exists": True, "$nin": [None, ""]},
        "$or": [
            {"resume_url": {"$exists": False}},
            {"resume_url": None},
            {"resume_url": ""},
        ],
    })

    profiles = await cursor.to_list(length=None)

    if not profiles:
        print("Nothing to backfill — every profile with a generated CV already has resume_url set.")
        return

    print(f"Found {len(profiles)} profile(s) to backfill:\n")

    updated = 0
    for profile in profiles:
        result = await seeker_profiles_collection.update_one(
            {"_id": profile["_id"]},
            {"$set": {"resume_url": profile["cv_url"]}},
        )
        if result.modified_count:
            updated += 1
            print(f"  [+] user_id={profile.get('user_id')} -> resume_url set from cv_url")

    print(f"\nDone. {updated} profile(s) updated. Affected seekers can now Apply immediately (no need to regenerate their CV).")


if __name__ == "__main__":
    asyncio.run(main())
