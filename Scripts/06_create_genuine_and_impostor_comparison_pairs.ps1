<#
Script: 06_create_genuine_and_impostor_comparison_pairs.ps1
Purpose: Generate a fixed list of genuine and impostor face-verification pairs.
Research stage: Methodology Preparation - Step 3.4.

Inputs:
  Original LFW dataset
  03_identity_split_manifest.csv
  08_image_selection_manifest.csv

Design:
  Random seed: 20261116
  Five distinct impostor enrolment identities per probe.
  All comparisons remain within Development or Test.
  Singleton identities are used as impostor probes only.
  The same fixed pair lists are intended for all three pipelines.

Outputs:
  10_genuine_pairs.csv
  11_impostor_pairs.csv
  12_all_comparison_pairs.csv
  13_pair_validation_report.txt

Note: This is computationally more expensive than the earlier preparation steps
because it repeatedly filters and shuffles candidate enrolment references.
Compatibility: Windows PowerShell 5.1
#>

$ErrorActionPreference = "Stop"

$dataset = "D:\Study\Applied Research Project\Final Project\lfw"
$folder = "D:\Study\Applied Research Project\Final Project\GitHub\facial-recognition-attendance-system\methodology_preparation\03_dataset_split"
$identityFile = Join-Path $folder "03_identity_split_manifest.csv"
$imageFile = Join-Path $folder "08_image_selection_manifest.csv"
$seed = 20261116
$impostorsPerProbe = 5

foreach ($path in @($dataset, $identityFile, $imageFile)) {
    if (-not (Test-Path $path)) { throw "Required input not found: $path" }
}

$identities = Import-Csv $identityFile
$selectedImages = Import-Csv $imageFile
if ($identities.Count -ne 5749) { throw "Unexpected identity count." }

$identityLookup = @{}
foreach ($person in $identities) { $identityLookup[$person.Identity] = $person }

$enrolments = @($selectedImages | Where-Object Role -eq "Enrolment")
$genuineProbes = @($selectedImages | Where-Object Role -eq "GenuineProbe")

if ($enrolments.Count -ne 1680) { throw "Expected 1680 enrolment images." }
if ($genuineProbes.Count -ne 4883) { throw "Expected 4883 genuine probes." }

$references = foreach ($item in $enrolments) {
    [PSCustomObject]@{
        Identity = $item.Identity
        Split = $item.Split
        RelativePath = $item.RelativePath
    }
}

# Add the one original image belonging to each singleton identity as an
# impostor probe. Singletons are not used as enrolment references.
$singletons = @($identities | Where-Object { [int]$_.ImageCount -eq 1 })
$singletonProbes = @()

foreach ($person in $singletons) {
    $identityFolder = Join-Path $dataset $person.Identity
    if (-not (Test-Path $identityFolder)) {
        throw "Missing singleton identity folder: $($person.Identity)"
    }

    $images = @(
        Get-ChildItem $identityFolder -File |
        Where-Object { $_.Extension -match '^\.(jpg|jpeg)$' }
    )
    if ($images.Count -ne 1) {
        throw "Expected exactly one image for $($person.Identity)."
    }

    $singletonProbes += [PSCustomObject]@{
        Identity = $person.Identity
        Split = $person.Split
        RelativePath = Join-Path $person.Identity $images[0].Name
    }
}

if ($singletonProbes.Count -ne 4069) { throw "Expected 4069 singleton probe images." }

$allProbes = @()
foreach ($probe in $genuineProbes) {
    $allProbes += [PSCustomObject]@{
        Identity = $probe.Identity
        Split = $probe.Split
        RelativePath = $probe.RelativePath
        ProbeCategory = "Genuine-capable identity"
    }
}
foreach ($probe in $singletonProbes) {
    $allProbes += [PSCustomObject]@{
        Identity = $probe.Identity
        Split = $probe.Split
        RelativePath = $probe.RelativePath
        ProbeCategory = "Single-image identity"
    }
}
if ($allProbes.Count -ne 8952) { throw "Unexpected total impostor probe count." }

# Genuine pairs: each genuine probe compared with its own identity's enrolment.
$genuinePairs = [System.Collections.Generic.List[object]]::new()
$genuineCounter = 0

foreach ($probe in $genuineProbes) {
    $reference = @($references | Where-Object Identity -eq $probe.Identity)
    if ($reference.Count -ne 1) {
        throw "Expected one enrolment reference for $($probe.Identity)."
    }
    if ($reference[0].Split -ne $probe.Split) {
        throw "Genuine comparison split mismatch: $($probe.Identity)"
    }
    if ($reference[0].RelativePath -eq $probe.RelativePath) {
        throw "Same image used as enrolment and probe: $($probe.Identity)"
    }

    $genuineCounter++
    $genuinePairs.Add([PSCustomObject]@{
        PairID = "G$($genuineCounter.ToString('000000'))"
        Split = $probe.Split
        ComparisonType = "Genuine"
        ReferenceIdentity = $reference[0].Identity
        ReferenceImage = $reference[0].RelativePath
        ProbeIdentity = $probe.Identity
        ProbeImage = $probe.RelativePath
        ExpectedOutcome = "Accept"
    })
}

# Impostor pairs: five different enrolment identities from the same split.
$impostorPairs = [System.Collections.Generic.List[object]]::new()
$rng = [System.Random]::new($seed)
$impostorCounter = 0

foreach ($probe in $allProbes) {
    $candidates = @(
        $references | Where-Object {
            $_.Split -eq $probe.Split -and $_.Identity -ne $probe.Identity
        }
    )
    if ($candidates.Count -lt $impostorsPerProbe) {
        throw "Not enough impostor references for $($probe.Identity)."
    }

    for ($i = $candidates.Count - 1; $i -gt 0; $i--) {
        $j = $rng.Next(0, $i + 1)
        $temp = $candidates[$i]
        $candidates[$i] = $candidates[$j]
        $candidates[$j] = $temp
    }

    for ($i = 0; $i -lt $impostorsPerProbe; $i++) {
        $reference = $candidates[$i]
        if ($reference.Identity -eq $probe.Identity) {
            throw "Invalid impostor identity match."
        }

        $impostorCounter++
        $impostorPairs.Add([PSCustomObject]@{
            PairID = "I$($impostorCounter.ToString('000000'))"
            Split = $probe.Split
            ComparisonType = "Impostor"
            ReferenceIdentity = $reference.Identity
            ReferenceImage = $reference.RelativePath
            ProbeIdentity = $probe.Identity
            ProbeImage = $probe.RelativePath
            ExpectedOutcome = "Reject"
        })
    }
}

$allPairs = @($genuinePairs.ToArray()) + @($impostorPairs.ToArray())

# Validation
$splitErrors = @($allPairs | Where-Object {
    $identityLookup[$_.ReferenceIdentity].Split -ne $_.Split -or
    $identityLookup[$_.ProbeIdentity].Split -ne $_.Split
})
$genuineErrors = @($genuinePairs | Where-Object {
    $_.ReferenceIdentity -ne $_.ProbeIdentity -or
    $_.ExpectedOutcome -ne "Accept"
})
$impostorErrors = @($impostorPairs | Where-Object {
    $_.ReferenceIdentity -eq $_.ProbeIdentity -or
    $_.ExpectedOutcome -ne "Reject"
})
$impostorGroups = $impostorPairs | Group-Object Split, ProbeIdentity, ProbeImage
$badImpostorCounts = @($impostorGroups | Where-Object Count -ne $impostorsPerProbe)
$badReferenceDuplicates = 0
foreach ($group in $impostorGroups) {
    $uniqueRefs = @($group.Group.ReferenceIdentity | Select-Object -Unique)
    if ($uniqueRefs.Count -ne $impostorsPerProbe) { $badReferenceDuplicates++ }
}
$missingPaths = @($allPairs | Where-Object {
    -not (Test-Path (Join-Path $dataset $_.ReferenceImage)) -or
    -not (Test-Path (Join-Path $dataset $_.ProbeImage))
})
$pairKeys = @($allPairs | ForEach-Object {
    "$($_.ComparisonType)|$($_.ReferenceIdentity)|$($_.ReferenceImage)|$($_.ProbeIdentity)|$($_.ProbeImage)"
} | Select-Object -Unique)
$duplicatePairCount = $allPairs.Count - $pairKeys.Count

$genuineDev = @($genuinePairs | Where-Object Split -eq "Development").Count
$genuineTest = @($genuinePairs | Where-Object Split -eq "Test").Count
$impostorDev = @($impostorPairs | Where-Object Split -eq "Development").Count
$impostorTest = @($impostorPairs | Where-Object Split -eq "Test").Count

$pass = ($genuinePairs.Count -eq 4883 -and $impostorPairs.Count -eq 44760 -and
    $splitErrors.Count -eq 0 -and $genuineErrors.Count -eq 0 -and
    $impostorErrors.Count -eq 0 -and $badImpostorCounts.Count -eq 0 -and
    $badReferenceDuplicates -eq 0 -and $missingPaths.Count -eq 0 -and
    $duplicatePairCount -eq 0)

$genuinePairs | Export-Csv (Join-Path $folder "10_genuine_pairs.csv") -NoTypeInformation
$impostorPairs | Export-Csv (Join-Path $folder "11_impostor_pairs.csv") -NoTypeInformation
$allPairs | Export-Csv (Join-Path $folder "12_all_comparison_pairs.csv") -NoTypeInformation

$report = @(
    "Genuine and impostor comparison pair validation"
    "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    "Random seed: $seed"
    "Impostor references per probe: $impostorsPerProbe"
    ""
    "Total impostor probes: $($allProbes.Count)"
    "Genuine comparisons: $($genuinePairs.Count)"
    "Impostor comparisons: $($impostorPairs.Count)"
    "Total comparison rows: $($allPairs.Count)"
    ""
    "Development genuine pairs: $genuineDev"
    "Test genuine pairs: $genuineTest"
    "Development impostor pairs: $impostorDev"
    "Test impostor pairs: $impostorTest"
    ""
    "Split errors: $($splitErrors.Count)"
    "Genuine pair errors: $($genuineErrors.Count)"
    "Impostor pair errors: $($impostorErrors.Count)"
    "Probe groups with incorrect impostor count: $($badImpostorCounts.Count)"
    "Probe groups with duplicate reference identities: $badReferenceDuplicates"
    "Missing image paths: $($missingPaths.Count)"
    "Duplicate comparison keys: $duplicatePairCount"
    ""
    $(if ($pass) { "PASS - pair generation and validation completed." } else { "FAIL - inspect the validation errors." })
)
$report | Set-Content (Join-Path $folder "13_pair_validation_report.txt")
$report | ForEach-Object { Write-Host $_ }

if (-not $pass) { throw "Comparison pair validation failed." }
