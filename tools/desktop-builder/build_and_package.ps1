<#
.SYNOPSIS
  Build the Linux desktop binary inside Docker and produce the studio ZIP in release/.

USAGE (PowerShell from repo root):
  .\tools\desktop-builder\build_and_package.ps1

This script builds the `desktop-builder` image and runs it. The container will
place output files into the repo's `release/` directory.
#>

param(
    [string]$ImageName = "myrhythm-desktop-builder:latest",
    [string]$ReleaseDir = "release"
)

Set-StrictMode -Version Latest

$root = Resolve-Path .
$releasePath = Join-Path $root $ReleaseDir
if (-not (Test-Path $releasePath)) { New-Item -ItemType Directory -Path $releasePath | Out-Null }

Write-Host "Building Docker image: $ImageName"
docker build -t $ImageName -f .\tools\desktop-builder\Dockerfile .
if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }

Write-Host "Running builder container (artifacts will appear in $releasePath)"
docker run --rm -v "$($releasePath):/src/release" -v "$($root):/src" $ImageName
if ($LASTEXITCODE -ne 0) { throw "Docker run failed" }

Write-Host "Done. Check the $ReleaseDir folder for artifacts (dist, release zip)."
