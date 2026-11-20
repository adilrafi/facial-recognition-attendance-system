<#
Script: 02_create_identity_inventory.ps1
Purpose: Count the original JPEG images for every LFW identity and summarise
         the distribution of images per identity.
Research stage: Methodology Preparation - Step 3.1.

Input:
  D:\Study\Applied Research Project\Final Project\lfw

Outputs (methodology_preparation\03_dataset_split):
  01_identity_image_counts.csv
  02_identity_distribution_summary.txt

Expected totals: 5,749 identities and 13,233 JPEG images.
Compatibility: Windows PowerShell 5.1
#>

$ErrorActionPreference = "Stop"

$dataset = "D:\Study\Applied Research Project\Final Project\lfw"
$folder = "D:\Study\Applied Research Project\Final Project\GitHub\facial-recognition-attendance-system\methodology_preparation\03_dataset_split"

if (-not (Test-Path $dataset)) { throw "Dataset folder not found: $dataset" }
New-Item -ItemType Directory -Path $folder -Force | Out-Null

$records = New-Object System.Collections.Generic.List[object]

foreach ($identityFolder in (Get-ChildItem -Path $dataset -Directory)) {
    $count = @(Get-ChildItem -Path $identityFolder.FullName -File |
        Where-Object { $_.Extension -match '^\.(jpg|jpeg)$' }).Count

    $records.Add([PSCustomObject]@{
        Identity = $identityFolder.Name
        ImageCount = $count
    })
}

$records = @($records | Sort-Object Identity)
$records | Export-Csv -Path (Join-Path $folder "01_identity_image_counts.csv") -NoTypeInformation

$distribution = $records | Group-Object ImageCount | Sort-Object { [int]$_.Name }
$totalImages = ($records | Measure-Object -Property ImageCount -Sum).Sum
$singletons = @($records | Where-Object { $_.ImageCount -eq 1 }).Count
$multiImage = @($records | Where-Object { $_.ImageCount -ge 2 }).Count

$lines = @(
    "LFW identity image-count inventory"
    "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Dataset: $dataset"
    "Total identities: $($records.Count)"
    "Total JPEG images counted: $totalImages"
    "Identities with exactly one image: $singletons"
    "Identities with at least two images: $multiImage"
    ""
    "Distribution (images per identity : number of identities)"
)
foreach ($group in $distribution) {
    $lines += "$($group.Name) : $($group.Count)"
}
$lines | Set-Content (Join-Path $folder "02_identity_distribution_summary.txt")

Write-Host "Inventory completed."
Write-Host "Identities: $($records.Count)"
Write-Host "Images: $totalImages"
Write-Host "Single-image identities: $singletons"
Write-Host "Multi-image identities: $multiImage"
Write-Host "Outputs: $folder"

if ($records.Count -ne 5749 -or $totalImages -ne 13233) {
    throw "Inventory totals do not match the verified dataset totals."
}
