import asyncio
import sys

from backend.core.scheduler import UserActivityScheduler

async def main():
    print("Running expire_subscriptions now...")
    sched = UserActivityScheduler()
    try:
        await sched.expire_subscriptions()
        print("expire_subscriptions completed")
    except Exception as e:
        print(f"Error running expire_subscriptions: {e}", file=sys.stderr)
        raise

if __name__ == '__main__':
    asyncio.run(main())
