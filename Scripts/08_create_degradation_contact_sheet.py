
from pathlib import Path, PureWindowsPath
import csv
import cv2
import numpy as np


# Project locations
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_ROOT = Path(
    r"D:\Study\Applied Research Project\Final Project\lfw"
)

PILOT_ROOT = (
    PROJECT_ROOT
    / "methodology_preparation"
    / "05_image_degradation"
    / "pilot_output"
)

MANIFEST_FILE = PILOT_ROOT / "pilot_manifest.csv"

# Image selected for visual inspection
PROBE_IMAGE = r"Abdullah_Gul\Abdullah_Gul_0011.jpg"

OUTPUT_FOLDER = PILOT_ROOT / "visual_inspection"

CONDITIONS = [
    "brightness_mild",
    "brightness_moderate",
    "brightness_severe",
    "resolution_mild",
    "resolution_moderate",
    "resolution_severe",
    "blur_mild",
    "blur_moderate",
    "blur_severe",
    "jpeg_mild",
    "jpeg_moderate",
    "jpeg_severe",
    "noise_mild",
    "noise_moderate",
    "noise_severe",
    "combined_mild",
    "combined_moderate",
    "combined_severe",
]

# Contact-sheet layout
CELL_WIDTH = 270
CELL_HEIGHT = 290
COLUMNS = 5
THUMBNAIL_SIZE = 250


def load_image(path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)

    if image is None:
        raise RuntimeError(f"Could not read image: {path}")

    return image


def main():

    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(MANIFEST_FILE)

    # Read the pilot manifest
    with MANIFEST_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        rows = list(csv.DictReader(file))

    selected_rows = {
        row["Condition"]: row
        for row in rows
        if row["ProbeImage"] == PROBE_IMAGE
    }

    missing_conditions = [
        condition
        for condition in CONDITIONS
        if condition not in selected_rows
    ]

    if missing_conditions:
        raise ValueError(
            f"Missing conditions: {missing_conditions}"
        )

    # Load the original clean image
    original_path = (
        DATASET_ROOT
        / Path(*PureWindowsPath(PROBE_IMAGE).parts)
    )

    original = load_image(original_path)

    images = [("CLEAN ORIGINAL", original)]

    # Load all 18 degraded images
    for condition in CONDITIONS:

        output_path = (
            PROJECT_ROOT
            / Path(
                *PureWindowsPath(
                    selected_rows[condition]["OutputPath"]
                ).parts
            )
        )

        image = load_image(output_path)
        images.append((condition, image))

    # Create contact sheet
    rows_needed = (len(images) + COLUMNS - 1) // COLUMNS

    sheet = np.full(
        (
            rows_needed * CELL_HEIGHT,
            COLUMNS * CELL_WIDTH,
            3,
        ),
        245,
        dtype=np.uint8,
    )

    for index, (label, image) in enumerate(images):

        row = index // COLUMNS
        column = index % COLUMNS

        x = column * CELL_WIDTH
        y = row * CELL_HEIGHT

        cv2.putText(
            sheet,
            label,
            (x + 8, y + 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )

        thumbnail = cv2.resize(
            image,
            (THUMBNAIL_SIZE, THUMBNAIL_SIZE),
            interpolation=cv2.INTER_AREA,
        )

        sheet[
            y + 32:y + 32 + THUMBNAIL_SIZE,
            x + 10:x + 10 + THUMBNAIL_SIZE,
        ] = thumbnail

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    output_file = (
        OUTPUT_FOLDER
        / "Abdullah_Gul_0011_contact_sheet.png"
    )

    if not cv2.imwrite(str(output_file), sheet):
        raise RuntimeError("Could not save contact sheet.")

    print("\nCONTACT SHEET CREATED")
    print("=====================")
    print(f"Original image: {PROBE_IMAGE}")
    print(f"Images displayed: {len(images)}")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()
