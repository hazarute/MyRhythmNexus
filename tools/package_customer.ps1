<#
.SYNOPSIS
  Paketleyici: tek bir .exe ve müşteri-özel config.json -> müşteriye özel ZIP üretir.

.PARAMETER ExePath
  Üretilecek .exe dosyasının yolu (zorunlu)

.PARAMETER BackendUrl
  Müşteriye ait backend API base URL (zorunlu)

.PARAMETER OutputDir
  Üretilen ZIP'in konacağı klasör (varsayılan: ./release)

.PARAMETER CustomerName
  Paket adı içinde kullanılacak müşteri etiketi (varsayılan: timestamp)

.PARAMETER LicenseServerUrl
  (Opsiyonel) Lisans server URL'si, config içine eklenir.

.EXAMPLE
  .\package_customer.ps1 -ExePath "dist\MyRhythmNexus.exe" -BackendUrl "https://acme.example.com/api/v1" -CustomerName "acme"

#>

param(
    [Parameter(Mandatory=$true)] [string] $ExePath,
    [Parameter(Mandatory=$true)] [string] $BackendUrl,
    [string] $OutputDir = "release",
    [string] $CustomerName = "",
    [string] $LicenseServerUrl = ""
)

Set-StrictMode -Version Latest

if (-not (Test-Path $ExePath)) {
    Write-Error "EXE not found: $ExePath"
    exit 1
}

if ([string]::IsNullOrWhiteSpace($CustomerName)) {
    $CustomerName = (Get-Date -Format "yyyyMMdd-HHmmss")
}

$product = "MyRhythmNexus"
$work = Join-Path -Path $env:TEMP -ChildPath "pack_$($product)_$CustomerName"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Path $work | Out-Null

# Copy exe
Copy-Item -Path $ExePath -Destination (Join-Path $work (Split-Path $ExePath -Leaf)) -Force

# Write config.json (only non-sensitive settings)
$cfg = @{ backend_urls = @($BackendUrl); settings = @{ theme = "dark" } }
if (-not [string]::IsNullOrWhiteSpace($LicenseServerUrl)) { $cfg.license_server_url = $LicenseServerUrl }
$cfgJson = $cfg | ConvertTo-Json -Depth 5
$cfgPath = Join-Path $work "config.json"
$cfgJson | Out-File -FilePath $cfgPath -Encoding UTF8

# Write a simple install.bat that copies files to user's AppData
$installBat = @"
@echo off
setlocal
set APPDIR=%APPDATA%\\MyRhythmNexus
if not exist "%APPDIR%" mkdir "%APPDIR%"
copy "%~dp0\$(Split-Path -Leaf $ExePath)" "%APPDIR%\$(Split-Path -Leaf $ExePath)" /Y
copy "%~dp0\config.json" "%APPDIR%\config.json" /Y
echo Kurulum tamamlandi. Uygulamayi baslatmak icin exe'yi calistirin.
pause
endlocal
"@

$installPath = Join-Path $work "install.bat"
Set-Content -Path $installPath -Value $installBat -Encoding ASCII

# Ensure output dir
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$zipName = "${product}-${CustomerName}.zip"
$zipPath = Join-Path -Path $OutputDir -ChildPath $zipName
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

Write-Host "Creating package $zipPath ..."
Compress-Archive -Path (Join-Path $work '*') -DestinationPath $zipPath -Force

# Compute SHA256
$hash = Get-FileHash -Path $zipPath -Algorithm SHA256
$hashFile = "$zipPath.sha256"
$hash.Hash | Out-File -FilePath $hashFile -Encoding ASCII

Write-Host "Package created: $zipPath"
Write-Host "Checksum: $($hash.Hash) -> $hashFile"

# Cleanup
Remove-Item -Recurse -Force $work

Write-Host "Done."
