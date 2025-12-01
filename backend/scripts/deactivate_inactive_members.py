#!/usr/bin/env python3
"""
Manual script to run the user activity scheduler for testing purposes.
This can be run independently or as a cron job.
"""

import asyncio
import sys
import os

# Add project root and backend to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.core.scheduler import UserActivityScheduler


async def main():
    """Run the scheduler manually for testing"""
    print("Starting manual user activity check...")

    scheduler = UserActivityScheduler()
    await scheduler.deactivate_inactive_members()

    print("Manual check completed.")


if __name__ == "__main__":
    asyncio.run(main())