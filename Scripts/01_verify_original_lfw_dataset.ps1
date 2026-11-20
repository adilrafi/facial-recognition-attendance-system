<#
Script: 01_verify_original_lfw_dataset.ps1
Purpose: Verify the original LFW archive checksum and inspect the extracted,
         unaligned LFW dataset.
Research stage: Methodology Preparation - Steps 1 and 2.

Inputs:
  D:\Study\Applied Research Project\Final Project\lfw.tgz
  D:\Study\Applied Research Project\Final Project\lfw

Outputs (saved in methodology_preparation\02_dataset_verification):
  01_archive_checksum.txt
  02_checksum_comparison.txt
  03_dataset_counts.txt
  04_image_dimensions.txt

Expected archive SHA-256:
  055F7D9C632D7370E6FB4AFC7468D40F970C34A80D4C6F50FFEC63F5A8D536C0

Compatibility: Windows PowerShell 5.1
#>

$ErrorActionPreference = "Stop"

$archive = "D:\Study\Applied Research Project\Final Project\lfw.tgz"
$dataset = "D:\Study\Applied Research Project\Final Project\lfw"
$output = "D:\Study\Applied Research Project\Final Project\GitHub\facial-recognition-attendance-system\methodology_preparation\02_dataset_verification"
$expectedHash = "055F7D9C632D7370E6FB4AFC7468D40F970C34A80D4C6F50FFEC63F5A8D536C0"

New-Item -ItemType Directory -Path $output -Force | Out-Null

foreach ($path in @($archive, $dataset)) {
    if (-not (Test-Path $path)) { throw "Required path not found: $path" }
}

# 1. Archive checksum
$hash = (Get-FileHash -Path $archive -Algorithm SHA256).Hash.ToUpper()
@(
    "LFW archive checksum verification"
    "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Archive: $archive"
    "Expected SHA-256: $expectedHash"
    "Actual SHA-256:   $hash"
) | Set-Content (Join-Path $output "01_archive_checksum.txt")

# 2. Checksum comparison
$status = if ($hash -eq $expectedHash) { "PASS - checksum matches" } else { "FAIL - checksum does not match" }
@(
    "Checksum comparison"
    "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Result: $status"
) | Set-Content (Join-Path $output "02_checksum_comparison.txt")

# 3. Dataset identity and image counts
$identityFolders = @(Get-ChildItem -Path $dataset -Directory)
$images = @(Get-ChildItem -Path $dataset -Recurse -File |
    Where-Object { $_.Extension -match '^\.(jpg|jpeg)$' })

@(
    "LFW extracted dataset counts"
    "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Dataset folder: $dataset"
    "Identity folders: $($identityFolders.Count)"
    "JPEG images: $($images.Count)"
) | Set-Content (Join-Path $output "03_dataset_counts.txt")

# 4. Image dimensions and readability
Add-Type -AssemblyName System.Drawing
$dimensionCounts = @{}
$unreadable = New-Object System.Collections.Generic.List[string]
$checked = 0

foreach ($file in $images) {
    $img = $null
    try {
        $img = [System.Drawing.Image]::FromFile($file.FullName)
        $key = "$($img.Width)x$($img.Height)"
        if (-not $dimensionCounts.ContainsKey($key)) { $dimensionCounts[$key] = 0 }
        $dimensionCounts[$key]++
        $checked++
    }
    catch {
        $unreadable.Add($file.FullName)
    }
    finally {
        if ($null -ne $img) { $img.Dispose() }
    }
}

$dimensionLines = @(
    "LFW image dimensions and readability"
    "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Images checked: $checked"
    "Unreadable images: $($unreadable.Count)"
    "Dimension distribution:"
)
foreach ($key in ($dimensionCounts.Keys | Sort-Object)) {
    $dimensionLines += "$key : $($dimensionCounts[$key])"
}
if ($unreadable.Count -gt 0) {
    $dimensionLines += "Unreadable image paths:"
    $dimensionLines += $unreadable
}
$dimensionLines | Set-Content (Join-Path $output "04_image_dimensions.txt")

Write-Host "Verification completed."
Write-Host "Identities: $($identityFolders.Count)"
Write-Host "JPEG images: $($images.Count)"
Write-Host "Readable images: $checked"
Write-Host "Unreadable images: $($unreadable.Count)"
Write-Host "Checksum result: $status"
Write-Host "Outputs: $output"

if ($hash -ne $expectedHash) { throw "Archive checksum validation failed." }
if ($identityFolders.Count -ne 5749 -or $images.Count -ne 13233) {
    throw "Dataset counts differ from the expected LFW counts; inspect the reports."
}
if ($unreadable.Count -gt 0) { throw "One or more images could not be read." }
