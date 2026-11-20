
from pathlib import Path, PureWindowsPath
import csv
import cv2
import numpy as np


# --------------------------------------------------
# PROJECT LOCATIONS
# --------------------------------------------------

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

# Separate output folder: existing contact sheet is preserved
OUTPUT_FOLDER = (
    PILOT_ROOT
    / "visual_inspection_additional"
)

# --------------------------------------------------
# SELECTION SETTINGS
# --------------------------------------------------

RANDOM_SEED = 20261119
NUMBER_OF_IMAGES = 5

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

# --------------------------------------------------
# CONTACT SHEET SETTINGS
# --------------------------------------------------

CELL_WIDTH = 270
CELL_HEIGHT = 290
COLUMNS = 5
THUMBNAIL_SIZE = 250


def load_image(path):

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)

    if image is None:
        raise RuntimeError(
            f"Could not read image: {path}"
        )

    return image


def create_contact_sheet(probe_image, selected_rows):

    identity = PureWindowsPath(probe_image).parts[0]

    original_path = (
        DATASET_ROOT
        / Path(*PureWindowsPath(probe_image).parts)
    )

    original = load_image(original_path)

    images = [
        ("CLEAN ORIGINAL", original)
    ]

    # Load the 18 existing degraded images
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

    rows_needed = (
        len(images) + COLUMNS - 1
    ) // COLUMNS

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

    filename = (
        f"{identity}__"
        f"{Path(probe_image).stem}"
        f"_contact_sheet.png"
    )

    output_file = OUTPUT_FOLDER / filename

    if not cv2.imwrite(str(output_file), sheet):

        raise RuntimeError(
            f"Could not save contact sheet: {output_file}"
        )

    return output_file


def main():

    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(MANIFEST_FILE)

    with MANIFEST_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        rows = list(csv.DictReader(file))

    # Group manifest entries by probe image.
    # Each probe should have all 18 conditions.

    probe_groups = {}

    for row in rows:

        probe = row["ProbeImage"]

        if probe not in probe_groups:
            probe_groups[probe] = {}

        probe_groups[probe][row["Condition"]] = row

    # Retain only complete probe groups
    complete_probes = {
        probe: conditions
        for probe, conditions in probe_groups.items()
        if all(
            condition in conditions
            for condition in CONDITIONS
        )
    }

    if not complete_probes:
        raise RuntimeError(
            "No complete pilot probe groups found."
        )

    # Group eligible probes by identity
    identity_groups = {}

    for probe in complete_probes:

        identity = PureWindowsPath(probe).parts[0]

        identity_groups.setdefault(
            identity, []
        ).append(probe)

    if len(identity_groups) < NUMBER_OF_IMAGES:

        raise RuntimeError(
            "Not enough different identities "
            "for the requested inspection."
        )

    # Select five different identities reproducibly
    rng = np.random.default_rng(RANDOM_SEED)

    identities = sorted(identity_groups.keys())

    selected_identities = rng.choice(
        identities,
        size=NUMBER_OF_IMAGES,
        replace=False,
    )

    selected_probes = []

    for identity in selected_identities:

        candidates = sorted(identity_groups[identity])

        selected_probe = rng.choice(candidates)

        selected_probes.append(selected_probe)

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Create a record of the selected images
    selection_file = (
        OUTPUT_FOLDER
        / "selected_inspection_images.csv"
    )

    with selection_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Identity",
            "ProbeImage",
            "RandomSeed",
        ])

        for probe in selected_probes:

            identity = PureWindowsPath(probe).parts[0]

            writer.writerow([
                identity,
                probe,
                RANDOM_SEED,
            ])

    # Create the five contact sheets
    print("\nADDITIONAL PILOT VISUAL INSPECTION")
    print("=================================")

    for index, probe in enumerate(
        selected_probes,
        start=1,
    ):

        output_file = create_contact_sheet(
            probe,
            complete_probes[probe],
        )

        print(f"\nImage {index}: {probe}")
        print(f"Contact sheet: {output_file}")

    print("\nINSPECTION COMPLETED")
    print("====================")
    print(f"Different identities: {NUMBER_OF_IMAGES}")
    print(f"Contact sheets created: {NUMBER_OF_IMAGES}")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Selection record: {selection_file}")


if __name__ == "__main__":
    main()
