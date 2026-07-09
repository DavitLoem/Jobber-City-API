#!/usr/bin/env python3
import asyncio
import sys
import os

# បន្ថែម Root Folder ទៅក្នុង System Path ដើម្បីឱ្យវាអាច Import ពី src បាន
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seeds.data_industries import seed_industries
from seeds.data_provinces import seed_provinces
from seeds.data_categories import seed_categories
from seeds.data_district import seed_districts
from seeds.master_data import seed_master_data

async def main():
    print("🎉 Database Seeding...\n" + "-"*40)
    
    # ហៅ Function បញ្ចូលទិន្នន័យម្តងមួយៗ
    # await seed_industries()
    # await seed_provinces()
    await seed_categories()
    # await seed_districts()
    # await seed_master_data()
    
    print("-" * 40 + "\n🎉 Seeding Completed Successfully!")

if __name__ == "__main__":
    # បញ្ជាឱ្យ Run Async Function
    asyncio.run(main())
    
# python seeds/run_seeds.py