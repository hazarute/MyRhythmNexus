<#
.SYNOPSIS
  Convenience runner for `license_server/scripts/*.py` script files.

.DESCRIPTION
  This helper sets `PYTHONPATH` to the repository root and runs the
  requested script. It can run locally (default) or use `railway run`
  to execute the script with environment variables from a Railway
  environment (e.g. production).

.EXAMPLES
  # Local execution (use a single string for Args):
  .\run.ps1 -Script create_license_cli -Args '--name "TugbaDansSpor" --email "tugbadanspor@gmail.com" --days 1825'

  # Run inside Railway environment (requires `railway` CLI logged in):
  .\run.ps1 -Script create_license_cli -Args '--name "TugbaDansSpor" --email "tugbadanspor@gmail.com" --days 1825' -UseRailway -RailwayEnv production

#>
param(
    [Parameter(Mandatory=$true)]
    [string]$Script,

    [string]$Args = "",

    [switch]$UseRailway,
    [string]$RailwayEnv = "production"
)

# Path to the requested script inside this folder
$scriptFile = Join-Path -Path $PSScriptRoot -ChildPath ("$Script.py")
if (-not (Test-Path $scriptFile)) {
    Write-Error "Script not found: $scriptFile"
    exit 1
}

if ($UseRailway) {
    # Run the script using Railway's environment variables (railway CLI must be installed)
    $cmd = "railway run -e $RailwayEnv python `"$scriptFile`" $Args"
    Write-Host "Running via Railway: $cmd"
    iex $cmd
} else {
    # Set PYTHONPATH to repo root so imports like `from license_server...` work
    $repoRoot = Split-Path -Parent -Path (Split-Path -Parent $PSScriptRoot)
    $env:PYTHONPATH = $repoRoot
    Write-Host "PYTHONPATH=$repoRoot"

    $cmd = "python `"$scriptFile`" $Args"
    Write-Host "Running locally: $cmd"
    iex $cmd
}
