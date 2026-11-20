
"""
Multiple-face detection inspection
==================================

Purpose:
    Inspect 20 different Development-set identities using MTCNN
    and YOLOv8n face detectors.

The script:
    - Selects one unique probe image from each of 20 identities.
    - Uses a fixed random seed for reproducibility.
    - Runs both detectors on every selected image.
    - Records the number of detected faces and bounding boxes.
    - Saves annotated copies for visual inspection.
    - Never modifies original LFW images or comparison pairs.
"""

from pathlib import Path, PureWindowsPath
import csv
import random
import sys

import cv2
from deepface import DeepFace


# ---------------------------------------------------------
# 1. PATHS AND SETTINGS
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
    / "multiple_face_inspection"
)

MANIFEST_FILE = OUTPUT_ROOT / "detection_results.csv"

RANDOM_SEED = 20261118
SAMPLE_SIZE = 20

DETECTORS = [
    "mtcnn",
    "yolov8n",
]


# ---------------------------------------------------------
# 2. SELECT 20 DIFFERENT DEVELOPMENT IDENTITIES
# ---------------------------------------------------------

def select_images():

    if not PAIR_FILE.exists():
        raise FileNotFoundError(PAIR_FILE)

    identity_images = {}

    with PAIR_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row["Split"] != "Development":
                continue

            relative_path = row["ProbeImage"]
            identity = PureWindowsPath(relative_path).parts[0]

            identity_images.setdefault(identity, set()).add(
                relative_path
            )

    if len(identity_images) < SAMPLE_SIZE:
        raise ValueError(
            "Not enough Development identities."
        )

    rng = random.Random(RANDOM_SEED)

    selected_identities = sorted(
        rng.sample(
            sorted(identity_images.keys()),
            SAMPLE_SIZE,
        )
    )

    selected = []

    for identity in selected_identities:

        candidates = sorted(identity_images[identity])
        relative_path = rng.choice(candidates)

        selected.append(
            (identity, relative_path)
        )

    return selected


# ---------------------------------------------------------
# 3. RUN ONE DETECTOR
# ---------------------------------------------------------

def detect_faces(image_path, detector):

    try:

        faces = DeepFace.extract_faces(
            img_path=str(image_path),
            detector_backend=detector,
            enforce_detection=True,
            align=False,
        )

        areas = []

        for face in faces:

            area = face.get("facial_area", {})
            confidence = face.get("confidence")

            areas.append({
                "x": area.get("x"),
                "y": area.get("y"),
                "w": area.get("w"),
                "h": area.get("h"),
                "confidence": confidence,
            })

        return {
            "status": "SUCCESS",
            "count": len(areas),
            "areas": areas,
            "error": "",
        }

    except Exception as error:

        if error.__class__.__name__ == "FaceNotDetected":

            return {
                "status": "NO_FACE_DETECTED",
                "count": 0,
                "areas": [],
                "error": "",
            }

        return {
            "status": "ERROR",
            "count": None,
            "areas": [],
            "error": (
                f"{error.__class__.__name__}: {error}"
            ),
        }


# ---------------------------------------------------------
# 4. SAVE ANNOTATED IMAGE
# ---------------------------------------------------------

def save_annotated_image(
    original,
    identity,
    detector,
    result,
):

    annotated = original.copy()

    for index, area in enumerate(result["areas"], start=1):

        x = area["x"]
        y = area["y"]
        w = area["w"]
        h = area["h"]

        if None in (x, y, w, h):
            continue

        x1 = int(x)
        y1 = int(y)
        x2 = int(x + w)
        y2 = int(y + h)

        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

        confidence = area["confidence"]

        label = f"Face {index}"

        if confidence is not None:
            label += f" ({confidence:.2f})"

        cv2.putText(
            annotated,
            label,
            (x1, max(15, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    cv2.putText(
        annotated,
        f"{identity} | {detector} | "
        f"Faces: {result['count']}",
        (5, 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 0, 255),
        1,
        cv2.LINE_AA,
    )

    output_file = (
        OUTPUT_ROOT
        / "annotated_images"
        / f"{identity}_{detector}.jpg"
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not cv2.imwrite(str(output_file), annotated):
        raise RuntimeError(
            f"Could not save annotated image: {output_file}"
        )

    return output_file


# ---------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------

def main():

    print("\nMULTIPLE-FACE DETECTION INSPECTION")
    print("==================================")

    print(f"Random seed: {RANDOM_SEED}")
    print(f"Sample size: {SAMPLE_SIZE} identities")
    print(f"Detectors: {', '.join(DETECTORS)}")

    if not DATASET_ROOT.exists():
        raise FileNotFoundError(DATASET_ROOT)

    if OUTPUT_ROOT.exists() and any(OUTPUT_ROOT.iterdir()):
        raise FileExistsError(
            "The output folder already contains files. "
            "Inspect it before running this script again."
        )

    selected = select_images()

    print(f"\nSelected identities: {len(selected)}")

    # Validate and load selected images.
    loaded_images = []

    for identity, relative_path in selected:

        image_path = (
            DATASET_ROOT
            / Path(*PureWindowsPath(relative_path).parts)
        )

        if not image_path.is_file():
            raise FileNotFoundError(image_path)

        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_COLOR,
        )

        if image is None:
            raise RuntimeError(
                f"Could not read image: {image_path}"
            )

        loaded_images.append(
            (identity, relative_path, image_path, image)
        )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    records = []

    for index, (
        identity,
        relative_path,
        image_path,
        image,
    ) in enumerate(loaded_images, start=1):

        print(
            f"\n[{index}/{SAMPLE_SIZE}] "
            f"{identity}: {relative_path}"
        )

        for detector in DETECTORS:

            result = detect_faces(
                image_path,
                detector,
            )

            if result["status"] == "ERROR":
                print(
                    f"  {detector}: ERROR - {result['error']}"
                )
            else:
                print(
                    f"  {detector}: "
                    f"{result['count']} face(s)"
                )

            annotated_path = save_annotated_image(
                image,
                identity,
                detector,
                result,
            )

            records.append({
                "Identity": identity,
                "Split": "Development",
                "ProbeImage": relative_path,
                "Detector": detector,
                "Status": result["status"],
                "FaceCount": result["count"],
                "FaceAreas": str(result["areas"]),
                "Error": result["error"],
                "AnnotatedImage": str(
                    annotated_path.relative_to(PROJECT_ROOT)
                ),
            })

    # Save results.
    fieldnames = [
        "Identity",
        "Split",
        "ProbeImage",
        "Detector",
        "Status",
        "FaceCount",
        "FaceAreas",
        "Error",
        "AnnotatedImage",
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
        writer.writerows(records)

    print("\nINSPECTION COMPLETED")
    print("====================")
    print(f"Identities inspected: {len(selected)}")
    print(f"Detector checks: {len(records)}")
    print(f"Expected checks: {SAMPLE_SIZE * len(DETECTORS)}")
    print(f"Results CSV: {MANIFEST_FILE}")
    print(f"Annotated images: {OUTPUT_ROOT / 'annotated_images'}")

    print("\nFACE COUNT SUMMARY")

    for detector in DETECTORS:

        detector_records = [
            row for row in records
            if row["Detector"] == detector
        ]

        counts = [
            row["FaceCount"]
            for row in detector_records
            if row["FaceCount"] is not None
        ]

        multiple = sum(
            count > 1 for count in counts
        )

        no_face = sum(
            row["Status"] == "NO_FACE_DETECTED"
            for row in detector_records
        )

        errors = sum(
            row["Status"] == "ERROR"
            for row in detector_records
        )

        print(f"\n{detector}")
        print(f"  Images checked: {len(detector_records)}")
        print(f"  Multiple faces: {multiple}")
        print(f"  No face detected: {no_face}")
        print(f"  Errors: {errors}")


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print("\nERROR")
        print("=====")
        print(error)
        sys.exit(1)
