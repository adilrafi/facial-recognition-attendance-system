
"""
Preparation 5 - Image Degradation Pilot

Purpose:
    Generate a small, reproducible pilot of degraded Development
    probe images so that degradation severity can be visually checked.

Important:
    - Original LFW images are never modified.
    - Enrolment/reference images are not degraded.
    - Only unique probe images from the Development split are selected.
    - Test images are not used in this pilot.
    - Each degradation is applied independently to the clean original.
    - Combined degradations are applied in a fixed order.
"""

from pathlib import Path, PureWindowsPath
import csv
import hashlib
import random
import sys

import cv2
import numpy as np


# ---------------------------------------------------------
# 1. PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_ROOT = Path(
    r"D:\Study\Applied Research Project\Final Project\lfw"
)

PAIR_FILE = (
    PROJECT_ROOT
    / "methodology_preparation"
    / "03_dataset_split"
    / "12_all_comparison_pairs.csv"
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "methodology_preparation"
    / "05_image_degradation"
    / "pilot_output"
)

MANIFEST_FILE = OUTPUT_ROOT / "pilot_manifest.csv"


# ---------------------------------------------------------
# 2. PILOT SETTINGS
# ---------------------------------------------------------

RANDOM_SEED = 20261118
PILOT_SAMPLE_SIZE = 50
EXPECTED_IMAGE_SIZE = (250, 250)


# Three severity levels for each degradation type.
SEVERITY_SETTINGS = {
    "brightness": {
        "mild": 0.8,
        "moderate": 0.6,
        "severe": 0.4,
    },
    "resolution": {
        "mild": 0.75,
        "moderate": 0.50,
        "severe": 0.25,
    },
    "blur": {
        "mild": 0.5,
        "moderate": 1.0,
        "severe": 1.5,
    },
    "jpeg": {
        "mild": 70,
        "moderate": 40,
        "severe": 20,
    },
    "noise": {
        "mild": 5,
        "moderate": 10,
        "severe": 20,
    },
}


# ---------------------------------------------------------
# 3. REPRODUCIBLE RANDOM SEED PER IMAGE AND CONDITION
# ---------------------------------------------------------

def get_noise_seed(relative_path, condition):
    """
    Generate a stable seed for each image and condition.

    This avoids relying on Python's process-dependent hash().
    """

    text = (
        f"{RANDOM_SEED}|{relative_path}|{condition}"
    )

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return int(digest[:8], 16)


# ---------------------------------------------------------
# 4. INDIVIDUAL DEGRADATION FUNCTIONS
# ---------------------------------------------------------

def apply_brightness(image, multiplier):
    result = image.astype(np.float32) * multiplier

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_resolution(image, scale):
    height, width = image.shape[:2]

    small_width = max(1, round(width * scale))
    small_height = max(1, round(height * scale))

    reduced = cv2.resize(
        image,
        (small_width, small_height),
        interpolation=cv2.INTER_AREA,
    )

    restored = cv2.resize(
        reduced,
        (width, height),
        interpolation=cv2.INTER_CUBIC,
    )

    return restored


def apply_blur(image, sigma):
    return cv2.GaussianBlur(
        image,
        (0, 0),
        sigmaX=sigma,
        sigmaY=sigma,
    )


def apply_jpeg_compression(image, quality):
    success, encoded = cv2.imencode(
        ".jpg",
        image,
        [cv2.IMWRITE_JPEG_QUALITY, int(quality)],
    )

    if not success:
        raise RuntimeError("JPEG encoding failed.")

    decoded = cv2.imdecode(
        encoded,
        cv2.IMREAD_COLOR,
    )

    if decoded is None:
        raise RuntimeError("JPEG decoding failed.")

    return decoded


def apply_noise(image, sigma, seed):
    rng = np.random.default_rng(seed)

    noise = rng.normal(
        loc=0.0,
        scale=sigma,
        size=image.shape,
    )

    result = image.astype(np.float32) + noise

    return np.clip(result, 0, 255).astype(np.uint8)


# ---------------------------------------------------------
# 5. APPLY ONE CONDITION
# ---------------------------------------------------------

def generate_condition(image, degradation, severity,
                       relative_path, condition_name):

    if degradation == "brightness":
        value = SEVERITY_SETTINGS["brightness"][severity]
        result = apply_brightness(image, value)
        parameters = f"brightness_multiplier={value}"

    elif degradation == "resolution":
        value = SEVERITY_SETTINGS["resolution"][severity]
        result = apply_resolution(image, value)
        parameters = f"resolution_scale={value}"

    elif degradation == "blur":
        value = SEVERITY_SETTINGS["blur"][severity]
        result = apply_blur(image, value)
        parameters = f"gaussian_sigma={value}"

    elif degradation == "jpeg":
        value = SEVERITY_SETTINGS["jpeg"][severity]
        result = apply_jpeg_compression(image, value)
        parameters = f"jpeg_quality={value}"

    elif degradation == "noise":
        value = SEVERITY_SETTINGS["noise"][severity]
        seed = get_noise_seed(relative_path, condition_name)

        result = apply_noise(image, value, seed)
        parameters = f"noise_sigma={value};seed={seed}"

    else:
        raise ValueError(
            f"Unknown degradation: {degradation}"
        )

    return result, parameters


# ---------------------------------------------------------
# 6. APPLY COMBINED CONDITIONS
# ---------------------------------------------------------

def generate_combined(image, severity, relative_path):

    result = image.copy()
    parameters = []

    # Fixed order:
    # brightness -> resolution -> blur -> noise -> JPEG

    brightness = SEVERITY_SETTINGS["brightness"][severity]
    result = apply_brightness(result, brightness)
    parameters.append(f"brightness={brightness}")

    resolution = SEVERITY_SETTINGS["resolution"][severity]
    result = apply_resolution(result, resolution)
    parameters.append(f"resolution={resolution}")

    blur = SEVERITY_SETTINGS["blur"][severity]
    result = apply_blur(result, blur)
    parameters.append(f"blur_sigma={blur}")

    noise = SEVERITY_SETTINGS["noise"][severity]
    condition_name = f"combined_{severity}"
    seed = get_noise_seed(relative_path, condition_name)

    result = apply_noise(result, noise, seed)
    parameters.append(f"noise_sigma={noise};seed={seed}")

    jpeg = SEVERITY_SETTINGS["jpeg"][severity]
    result = apply_jpeg_compression(result, jpeg)
    parameters.append(f"jpeg_quality={jpeg}")

    return result, ";".join(parameters)


# ---------------------------------------------------------
# 7. LOAD UNIQUE DEVELOPMENT PROBES
# ---------------------------------------------------------

def load_development_probes():

    if not PAIR_FILE.exists():
        raise FileNotFoundError(
            f"Comparison-pair file not found: {PAIR_FILE}"
        )

    unique_probes = set()

    with PAIR_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "Split",
            "ProbeImage",
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(
                "Comparison-pair CSV is missing required columns."
            )

        for row in reader:

            if row["Split"] == "Development":
                unique_probes.add(row["ProbeImage"])

    probes = sorted(unique_probes)

    print(f"Unique Development probes: {len(probes)}")

    if len(probes) < PILOT_SAMPLE_SIZE:
        raise ValueError(
            "Not enough Development probes for the pilot."
        )

    rng = random.Random(RANDOM_SEED)

    selected = sorted(
        rng.sample(probes, PILOT_SAMPLE_SIZE)
    )

    return selected


# ---------------------------------------------------------
# 8. MAIN PILOT GENERATION
# ---------------------------------------------------------

def main():

    print("\nIMAGE DEGRADATION PILOT")
    print("======================")

    print(f"Project: {PROJECT_ROOT}")
    print(f"Dataset: {DATASET_ROOT}")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Pilot sample size: {PILOT_SAMPLE_SIZE}")

    if not DATASET_ROOT.exists():
        raise FileNotFoundError(
            f"Dataset folder not found: {DATASET_ROOT}"
        )

    if OUTPUT_ROOT.exists() and any(OUTPUT_ROOT.iterdir()):
        raise FileExistsError(
            "Pilot output folder already contains files. "
            "Please inspect it before running again. "
            "This script will not overwrite existing output."
        )

    selected_probes = load_development_probes()

    # Validate selected input images before creating output.
    source_images = []

    for relative_path in selected_probes:

        source_path = (
            DATASET_ROOT
            / Path(*PureWindowsPath(relative_path).parts)
        )

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Probe image not found: {source_path}"
            )

        image = cv2.imread(
            str(source_path),
            cv2.IMREAD_COLOR,
        )

        if image is None:
            raise RuntimeError(
                f"Could not read image: {source_path}"
            )

        if (image.shape[1], image.shape[0]) != EXPECTED_IMAGE_SIZE:
            raise ValueError(
                f"Unexpected image dimensions: {relative_path} "
                f"{image.shape[1]}x{image.shape[0]}"
            )

        source_images.append(
            (relative_path, source_path, image)
        )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    manifest_rows = []

    degradations = [
        "brightness",
        "resolution",
        "blur",
        "jpeg",
        "noise",
    ]

    severities = [
        "mild",
        "moderate",
        "severe",
    ]

    total_generated = 0

    for index, (relative_path, source_path, original) in enumerate(
        source_images,
        start=1,
    ):

        print(
            f"\nProcessing {index}/{len(source_images)}: "
            f"{relative_path}"
        )

        relative_parts = PureWindowsPath(relative_path).parts

        # Generate 15 individual conditions.
        for degradation in degradations:

            for severity in severities:

                condition = f"{degradation}_{severity}"

                degraded, parameters = generate_condition(
                    original,
                    degradation,
                    severity,
                    relative_path,
                    condition,
                )

                output_path = (
                    OUTPUT_ROOT
                    / "Development"
                    / condition
                    / Path(*relative_parts)
                ).with_suffix(".png")

                output_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                if not cv2.imwrite(str(output_path), degraded):
                    raise RuntimeError(
                        f"Could not save: {output_path}"
                    )

                manifest_rows.append({
                    "Split": "Development",
                    "ProbeImage": relative_path,
                    "Condition": condition,
                    "Severity": severity,
                    "Parameters": parameters,
                    "OutputPath": str(
                        output_path.relative_to(PROJECT_ROOT)
                    ),
                    "Width": degraded.shape[1],
                    "Height": degraded.shape[0],
                })

                total_generated += 1

        # Generate 3 combined conditions.
        for severity in severities:

            condition = f"combined_{severity}"

            degraded, parameters = generate_combined(
                original,
                severity,
                relative_path,
            )

            output_path = (
                OUTPUT_ROOT
                / "Development"
                / condition
                / Path(*relative_parts)
            ).with_suffix(".png")

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if not cv2.imwrite(str(output_path), degraded):
                raise RuntimeError(
                    f"Could not save: {output_path}"
                )

            manifest_rows.append({
                "Split": "Development",
                "ProbeImage": relative_path,
                "Condition": condition,
                "Severity": severity,
                "Parameters": parameters,
                "OutputPath": str(
                    output_path.relative_to(PROJECT_ROOT)
                ),
                "Width": degraded.shape[1],
                "Height": degraded.shape[0],
            })

            total_generated += 1

    # Save the generation manifest.
    fieldnames = [
        "Split",
        "ProbeImage",
        "Condition",
        "Severity",
        "Parameters",
        "OutputPath",
        "Width",
        "Height",
    ]

    with MANIFEST_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(manifest_rows)

    print("\nPILOT GENERATION COMPLETED")
    print("==========================")
    print(f"Selected probe images: {len(selected_probes)}")
    print(f"Conditions per image: 18")
    print(f"Generated images: {total_generated}")
    print(f"Expected images: {PILOT_SAMPLE_SIZE * 18}")
    print(f"Manifest: {MANIFEST_FILE}")
    print(f"Output folder: {OUTPUT_ROOT}")


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print("\nERROR")
        print("=====")
        print(error)
        sys.exit(1)
