<#
Script: 03_create_identity_development_test_split.ps1
Purpose: Create a fresh, reproducible identity-level development/test split.
         Stratification preserves the four image-count groups.
Research stage: Methodology Preparation - Step 3.2.

Input:
  01_identity_image_counts.csv

Design:
  Development proportion: 30%
  Test proportion: 70%
  Random seed: 20261113
  Categories: Single image, 2-5 images, 6-10 images, more than 10 images.

Outputs:
  03_identity_split_manifest.csv
  04_development_identities.csv
  05_test_identities.csv
  06_identity_split_validation.txt

Note: This is a fresh split. It does not import or reuse previous split files.
Compatibility: Windows PowerShell 5.1
#>

$ErrorActionPreference = "Stop"

$folder = "D:\Study\Applied Research Project\Final Project\GitHub\facial-recognition-attendance-system\methodology_preparation\03_dataset_split"
$inputFile = Join-Path $folder "01_identity_image_counts.csv"
$seed = 20261113
$developmentProportion = 0.30

if (-not (Test-Path $inputFile)) { throw "Input file not found: $inputFile" }

$inventory = @(Import-Csv $inputFile)
if ($inventory.Count -ne 5749) { throw "Expected 5,749 identities." }

foreach ($item in $inventory) { $item.ImageCount = [int]$item.ImageCount }

$categorized = foreach ($item in $inventory) {
    $category = if ($item.ImageCount -eq 1) {
        "Single image"
    } elseif ($item.ImageCount -le 5) {
        "2-5 images"
    } elseif ($item.ImageCount -le 10) {
        "6-10 images"
    } else {
        "More than 10 images"
    }

    [PSCustomObject]@{
        Identity = $item.Identity
        ImageCount = $item.ImageCount
        Category = $category
    }
}

$rng = [System.Random]::new($seed)
$manifest = New-Object System.Collections.Generic.List[object]

foreach ($categoryGroup in ($categorized | Group-Object Category)) {
    $members = @($categoryGroup.Group)

    # Fisher-Yates shuffle using the fixed random seed.
    for ($i = $members.Count - 1; $i -gt 0; $i--) {
        $j = $rng.Next(0, $i + 1)
        $temp = $members[$i]
        $members[$i] = $members[$j]
        $members[$j] = $temp
    }

    $developmentCount = [int][Math]::Round(
        $members.Count * $developmentProportion,
        [MidpointRounding]::AwayFromZero
    )

    for ($i = 0; $i -lt $members.Count; $i++) {
        $split = if ($i -lt $developmentCount) { "Development" } else { "Test" }

        $manifest.Add([PSCustomObject]@{
            Identity = $members[$i].Identity
            ImageCount = $members[$i].ImageCount
            Category = $members[$i].Category
            Split = $split
        })
    }
}

$manifestArray = @($manifest | Sort-Object Identity)
$development = @($manifestArray | Where-Object Split -eq "Development")
$test = @($manifestArray | Where-Object Split -eq "Test")
$overlap = @(
    $development.Identity | Where-Object { $_ -in $test.Identity }
)

$manifestArray | Export-Csv (Join-Path $folder "03_identity_split_manifest.csv") -NoTypeInformation
$development | Export-Csv (Join-Path $folder "04_development_identities.csv") -NoTypeInformation
$test | Export-Csv (Join-Path $folder "05_test_identities.csv") -NoTypeInformation

$lines = @(
    "Identity-level development/test split validation"
    "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Random seed: $seed"
    "Development proportion: 30%"
    "Test proportion: 70%"
    "Total identities: $($manifestArray.Count)"
    "Development identities: $($development.Count)"
    "Test identities: $($test.Count)"
    "Identity overlap: $($overlap.Count)"
    ""
    "Category allocation:"
)
foreach ($category in @("Single image", "2-5 images", "6-10 images", "More than 10 images")) {
    $devCount = @($development | Where-Object Category -eq $category).Count
    $testCount = @($test | Where-Object Category -eq $category).Count
    $lines += "$category : Development=$devCount; Test=$testCount"
}
$pass = ($manifestArray.Count -eq 5749 -and $development.Count -eq 1725 -and
         $test.Count -eq 4024 -and $overlap.Count -eq 0)
$lines += ""
$lines += if ($pass) { "PASS - all identities assigned exactly once; no identity leakage." } else { "FAIL - inspect split outputs." }
$lines | Set-Content (Join-Path $folder "06_identity_split_validation.txt")

$lines | ForEach-Object { Write-Host $_ }
if (-not $pass) { throw "Identity split validation failed." }
