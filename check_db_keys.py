#!/usr/bin/env python3
"""
Quick database check to verify API keys
"""
import asyncio
from app.models.database import db_manager

async def check_keys():
    await db_manager.initialize()
    result = await db_manager.execute_query(
        'SELECT key_id, name, permissions, created_at FROM api_keys ORDER BY created_at DESC LIMIT 5'
    )
    print('Recent API keys:')
    for row in result:
        print(f'  {row["key_id"]} - {row["name"]} - {row["created_at"]}')
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_keys())
