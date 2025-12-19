import asyncio
import secrets
from typing import Set
import argparse

from sqlalchemy.future import select

from backend.core.database import SessionLocal
from backend.models.operation import SubscriptionQrCode


MAX_ATTEMPTS = 10


async def rotate_tokens(only_active: bool, dry_run: bool) -> int:
    async with SessionLocal() as session:
        # Load all QR code rows
        query = select(SubscriptionQrCode)
        if only_active:
            query = query.where(SubscriptionQrCode.is_active == True)

        result = await session.execute(query)
        rows = result.scalars().all()

        if not rows:
            print("No subscription QR codes found to update.")
            return 0

        # Build set of existing tokens (all in DB) to avoid collisions
        all_tokens_q = await session.execute(select(SubscriptionQrCode.qr_token))
        existing_tokens: Set[str] = set(t for (t,) in all_tokens_q.all() if t)

        new_tokens_assigned: Set[str] = set()
        updates = []

        for qr in rows:
            # Remove current token from existing set so we can reuse its value space
            if qr.qr_token in existing_tokens:
                existing_tokens.remove(qr.qr_token)

            for attempt in range(MAX_ATTEMPTS):
                candidate = secrets.token_hex(16).upper()
                if candidate not in existing_tokens and candidate not in new_tokens_assigned:
                    new_tokens_assigned.add(candidate)
                    updates.append((qr.id, qr.qr_token, candidate))
                    qr.qr_token = candidate
                    break
            else:
                raise RuntimeError(f"Unable to generate unique token for qr id={qr.id} after {MAX_ATTEMPTS} attempts")

        print(f"Prepared {len(updates)} updates.")
        if dry_run:
            for uid, old, new in updates[:50]:
                print(f"id={uid}: {old} -> {new}")
            if len(updates) > 50:
                print(f"...and {len(updates)-50} more")
            return len(updates)

        # Apply updates and commit
        await session.commit()
        print(f"Committed {len(updates)} QR token updates.")
        return len(updates)


def main():
    parser = argparse.ArgumentParser(description="Rotate subscription QR tokens to secure 32-char hex tokens")
    parser.add_argument("--only-active", action="store_true", help="Only rotate tokens for active QR codes")
    parser.add_argument("--yes", action="store_true", help="Don't prompt for confirmation")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes but do not commit")
    args = parser.parse_args()

    if not args.yes:
        confirm = input(f"Rotate QR tokens (only_active={args.only_active})? This will update DB. Continue? [y/N]: ")
        if confirm.lower() not in ("y", "yes"):
            print("Aborted by user.")
            return

    count = asyncio.run(rotate_tokens(args.only_active, args.dry_run))
    print(f"Done. {count} tokens rotated.")


if __name__ == "__main__":
    main()
