<#
Script: 05_select_enrolment_and_genuine_probe_images.ps1
Purpose: Select one original enrolment image per identity with at least two
         images, then select up to 10 different original genuine probe images.
Research stage: Methodology Preparation - Step 3.3 (image selection).

Inputs:
  Original LFW image folders
  03_identity_split_manifest.csv

Design:
  Random seed: 20261114
  Maximum genuine probes per eligible identity: 10
  One image is selected for enrolment; probes are selected without replacement.
  Single-image identities are not selected as enrolment/genuine pairs.

Outputs:
  08_image_selection_manifest.csv
  09_image_selection_validation.txt

CSV columns:
  Identity, Split, Role, ProbeNumber, RelativePath
Compatibility: Windows PowerShell 5.1
#>

$ErrorActionPreference = "Stop"

$dataset = "D:\Study\Applied Research Project\Final Project\lfw"
$folder = "D:\Study\Applied Research Project\Final Project\GitHub\facial-recognition-attendance-system\methodology_preparation\03_dataset_split"
$identityFile = Join-Path $folder "03_identity_split_manifest.csv"
$seed = 20261114
$maxProbes = 10

if (-not (Test-Path $dataset)) { throw "Dataset not found: $dataset" }
if (-not (Test-Path $identityFile)) { throw "Identity split manifest not found." }

$identities = @(Import-Csv $identityFile)
$rng = [System.Random]::new($seed)
$selection = New-Object System.Collections.Generic.List[object]

foreach ($person in $identities) {
    $imageFiles = @(
        Get-ChildItem (Join-Path $dataset $person.Identity) -File |
        Where-Object { $_.Extension -match '^\.(jpg|jpeg)$' } |
        Sort-Object Name
    )

    if ($imageFiles.Count -ne [int]$person.ImageCount) {
        throw "Image count mismatch for identity $($person.Identity)."
    }

    if ($imageFiles.Count -lt 2) { continue }

    # Shuffle a copy of this identity's original images.
    for ($i = $imageFiles.Count - 1; $i -gt 0; $i--) {
        $j = $rng.Next(0, $i + 1)
        $temp = $imageFiles[$i]
        $imageFiles[$i] = $imageFiles[$j]
        $imageFiles[$j] = $temp
    }

    $enrolment = $imageFiles[0]
    $selection.Add([PSCustomObject]@{
        Identity = $person.Identity
        Split = $person.Split
        Role = "Enrolment"
        ProbeNumber = 0
        RelativePath = Join-Path $person.Identity $enrolment.Name
    })

    $availableProbeCount = [Math]::Min($maxProbes, $imageFiles.Count - 1)
    for ($i = 1; $i -le $availableProbeCount; $i++) {
        $selection.Add([PSCustomObject]@{
            Identity = $person.Identity
            Split = $person.Split
            Role = "GenuineProbe"
            ProbeNumber = $i
            RelativePath = Join-Path $person.Identity $imageFiles[$i].Name
        })
    }
}

$rows = @($selection)
$enrolments = @($rows | Where-Object Role -eq "Enrolment")
$probes = @($rows | Where-Object Role -eq "GenuineProbe")
$duplicatePaths = @($rows | Group-Object RelativePath | Where-Object Count -gt 1)
$badIdentities = @(
    $enrolments | Group-Object Identity | Where-Object Count -ne 1
)
$badProbeCaps = @(
    $probes | Group-Object Identity | Where-Object Count -gt $maxProbes
)

$rows | Export-Csv (Join-Path $folder "08_image_selection_manifest.csv") -NoTypeInformation

$devEnrol = @($enrolments | Where-Object Split -eq "Development").Count
$testEnrol = @($enrolments | Where-Object Split -eq "Test").Count
$devProbes = @($probes | Where-Object Split -eq "Development").Count
$testProbes = @($probes | Where-Object Split -eq "Test").Count

$pass = ($enrolments.Count -eq 1680 -and $probes.Count -eq 4883 -and
         $duplicatePaths.Count -eq 0 -and $badIdentities.Count -eq 0 -and
         $badProbeCaps.Count -eq 0)

$lines = @(
    "Enrolment and genuine probe image selection validation"
    "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Random seed: $seed"
    "Maximum genuine probes per identity: $maxProbes"
    "Eligible identities: $($enrolments.Count)"
    "Enrolment images selected: $($enrolments.Count)"
    "Genuine probe images selected: $($probes.Count)"
    "Total selected images: $($rows.Count)"
    ""
    "Development enrolment images: $devEnrol"
    "Test enrolment images: $testEnrol"
    "Development genuine probes: $devProbes"
    "Test genuine probes: $testProbes"
    ""
    "Duplicate selected image paths: $($duplicatePaths.Count)"
    "Enrolment count errors: $($badIdentities.Count)"
    "Identities exceeding probe cap: $($badProbeCaps.Count)"
    ""
    $(if ($pass) { "PASS" } else { "FAIL - inspect selection output." })
)
$lines | Set-Content (Join-Path $folder "09_image_selection_validation.txt")
$lines | ForEach-Object { Write-Host $_ }

if (-not $pass) { throw "Image selection validation failed." }
