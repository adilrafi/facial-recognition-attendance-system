<#
Script: 04_assess_genuine_comparison_capacity.ps1
Purpose: Assess how many identities can support genuine verification comparisons
         and estimate the available probe-image capacity in each split.
Research stage: Methodology Preparation - Step 3.3 (capacity assessment).

Inputs:
  01_identity_image_counts.csv
  03_identity_split_manifest.csv

Output:
  07_genuine_comparison_capacity.txt

A genuine-capable identity has at least two original images. One image can be
reserved for enrolment; the remaining images are potential genuine probes.
Compatibility: Windows PowerShell 5.1
#>

$ErrorActionPreference = "Stop"

$folder = "D:\Study\Applied Research Project\Final Project\GitHub\facial-recognition-attendance-system\methodology_preparation\03_dataset_split"
$identityFile = Join-Path $folder "03_identity_split_manifest.csv"

if (-not (Test-Path $identityFile)) { throw "Split manifest not found: $identityFile" }

$identities = @(Import-Csv $identityFile)
foreach ($person in $identities) { $person.ImageCount = [int]$person.ImageCount }

$lines = @(
    "Genuine comparison capacity assessment"
    "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Potential probes are calculated as ImageCount minus one enrolment image."
    "This is capacity before applying the maximum of 10 probes per identity."
    ""
)

foreach ($splitName in @("Development", "Test")) {
    $group = @($identities | Where-Object Split -eq $splitName)
    $eligible = @($group | Where-Object ImageCount -ge 2)
    $singletons = @($group | Where-Object ImageCount -eq 1)
    $potential = @($eligible | ForEach-Object { $_.ImageCount - 1 })
    $totalPotential = ($potential | Measure-Object -Sum).Sum
    $sorted = @($potential | Sort-Object)
    $median = if ($sorted.Count % 2 -eq 1) {
        $sorted[[int][Math]::Floor($sorted.Count / 2)]
    } else {
        ($sorted[$sorted.Count / 2 - 1] + $sorted[$sorted.Count / 2]) / 2
    }
    $max = ($potential | Measure-Object -Maximum).Maximum
    $over10 = @($potential | Where-Object { $_ -gt 10 }).Count
    $over20 = @($potential | Where-Object { $_ -gt 20 }).Count

    $lines += "$splitName"
    $lines += "Total identities: $($group.Count)"
    $lines += "Eligible for genuine: $($eligible.Count)"
    $lines += "Singletons: $($singletons.Count)"
    $lines += "Potential genuine probe images if one image is reserved for enrolment: $totalPotential"
    $lines += "Median potential probes per eligible identity: $median"
    $lines += "Maximum potential probes for one identity: $max"
    $lines += "Identities with more than 10 potential probes: $over10"
    $lines += "Identities with more than 20 potential probes: $over20"
    $lines += ""
}

$lines | Set-Content (Join-Path $folder "07_genuine_comparison_capacity.txt")
$lines | ForEach-Object { Write-Host $_ }
