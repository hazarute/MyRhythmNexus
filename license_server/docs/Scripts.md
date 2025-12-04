# License Server — Admin Scripts

This document describes the helper scripts located in `license_server/scripts/`. These are small CLI utilities intended for development and administrative use to manage customers and licenses in the license server database.

Important notes
- These scripts operate directly against the License Server database configured via `license_server/database.py` and the environment variables your app uses (for development typically an SQLite file). In production you should run safe admin tools only against a properly secured and backed-up database.
- When running from the repo root on Windows PowerShell, set `PYTHONPATH` to the repository root so the `license_server` package can be imported. Example:

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/list_customer_licenses.py --all
```

- Many scripts are interactive and will prompt you for confirmation before making changes. Read prompts carefully.
- `private.pem` currently exists in the repo for development convenience. Do NOT commit production private keys to git; use your secrets manager in production.

Scripts
-------

1) `create_license_cli.py`

- Purpose: Create a `Customer` and one `License` for that customer. Useful to bootstrap test and demo licenses.
- Behavior:
  - Creates a `Customer` row (name, email, optional metadata).
  - Creates a `License` row associated to the customer with an auto-generated `license_key`, expiry date, features JSON, and optional `hardware_id` (HWID).
  - Prints the created `license_key` and expiry.
- Usage examples:

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/create_license_cli.py --name "FitLife Studio" --email contact@fitlife.com --days 365
# interactive: omit args and follow prompts
```

2) `reset_hwid_cli.py`

- Purpose: Reset the `hardware_id` (HWID) associated with an existing license or licenses for a customer, typically when a device is replaced.
- Behavior:
  - Prompts to select a customer (or accepts `--email`).
  - Shows matching licenses and allows selecting one or more.
  - Sets `hardware_id` to a new value (or clears it) for the selected licenses.
  - Requires confirmation before updating.
- Usage example:

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/reset_hwid_cli.py --email contact@fitlife.com
```

3) `add_license_for_customer.py`

- Purpose: Add an additional license for an existing customer (useful for multi-device or multi-seat purchases).
- Behavior:
  - Accepts `--email` or will prompt for the customer email.
  - Creates a new `License` row for the given customer with options for expiry days and features.
  - Prints the new `license_key`.
- Usage example:

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/add_license_for_customer.py --email contact@fitlife.com --days 365
```

4) `delete_license_cli.py`

- Purpose: Soft-delete (set `is_active=False`) or hard-delete license rows.
- Behavior:
  - Find customer by `--email` (or interactive prompt).
  - List licenses and allow selecting specific license(s) by index, `all`, or license key.
  - By default performs a soft-delete (sets `is_active=False`). Use `--hard` to remove the DB row.
  - Requires typing `yes` to confirm destructive changes.
- Usage examples:

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/delete_license_cli.py --email contact@fitlife.com --license-key MRN-XXXX --hard
python license_server/scripts/delete_license_cli.py --email contact@fitlife.com    # interactive choose
```

5) `list_customer_licenses.py`

- Purpose: Read-only helper to list customers and their licenses.
- Behavior:
  - `--all`: list all customers and their licenses.
  - `--email <address>`: show a single customer's licenses.
  - `--active-only`: only show active licenses.
  - Prints `license_key`, `active` status, `expires` timestamp, `hwid`, and `features` JSON.
- Usage examples:

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/list_customer_licenses.py --all
python license_server/scripts/list_customer_licenses.py --email contact@fitlife.com --active-only
```

Other utilities
---------------

- `license_server/generate_keys.py`: convenience script to generate a new RSA private/public key pair for development. In production you should generate and store keys securely and never commit private keys to source control.

Operational recommendations
-------------------------

- For safety, run destructive scripts (`delete_license_cli.py`, `reset_hwid_cli.py`) against a database backup or in a staging environment first.
- In automation (CI / admin tooling) prefer using an authenticated admin API rather than connecting directly to the database. If you need automation now, you can wrap these scripts with `--yes` / `--dry-run` flags (we can add those on request).
- Ensure the `public.pem` used by the desktop client matches the `private.pem` used by the license server for signing. Rotate keys when moving to production and update clients accordingly.

Troubleshooting
---------------

- Module import errors when running scripts? Make sure `PYTHONPATH` is set to the repo root as shown above.
- Database connection errors? Check `license_server/database.py` and the `LICENSE_DATABASE_URL` environment variable used by the license server.

Next improvements (optional)
---------------------------

- Add `--dry-run` and `--json` output modes to the scripts for better automation support.
- Add a small set of unit tests for critical behaviors (create, delete, reset) using a temporary test DB.
- Provide an authenticated admin HTTP API for all operations so scripts don't need direct DB access.

If you want, I can add `--dry-run` and `--json` to the key scripts next — which would you like first?
