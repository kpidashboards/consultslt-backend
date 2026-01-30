import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["consultslt_db"]
    print(await db.list_collection_names())

asyncio.run(main())
