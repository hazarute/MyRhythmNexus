# Running scripts in `license_server/scripts`

This folder contains small admin/dev scripts (e.g. `create_license_cli.py`).
Use the provided `run.ps1` helper to run them easily on Windows PowerShell.

Examples

- Local run (sets `PYTHONPATH` automatically):

```powershell
.
cd license_server\scripts
.
\run.ps1 -Script create_license_cli -Args '--name "TugbaDansSpor" --email "tugbadanspor@gmail.com" --days 1825'
```

- Run using Railway environment (requires `railway` CLI logged in):

```powershell
cd license_server\scripts
.
\run.ps1 -Script create_license_cli -Args '--name "TugbaDansSpor" --email "tugbadanspor@gmail.com" --days 1825' -UseRailway -RailwayEnv production
```

Notes
- `Args` is a single string that will be appended to the Python command. Include quotes where necessary.
- Local execution sets `PYTHONPATH` to the repository root so imports like `from license_server...` work.
- Using `-UseRailway` will run the script with environment variables from the selected Railway environment (`-RailwayEnv`).

Security
- Do NOT store private keys in the repo. When using `-UseRailway`, the Railway environment variables (e.g. `LICENSE_PRIVATE_KEY`) will be available to the script without adding them to the repo.

If you want a cross-shell wrapper (bash/mac), tell me and I'll add a small shell script equivalent.
