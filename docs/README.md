# Research Timeline

**Project:** Design and Evaluation of a Web-Based Facial Recognition System for Student Attendance Management in Online Learning Environments

This document records the chronological progress of the research project, including dataset preparation, experimental development, implementation, validation and important research milestones.

## November 2026

### 13 November 2026
- Completed identity-based Development and Test dataset splitting.
- Used random seed 20261113.
- Verified that there was no identity overlap between the two splits.

### 14 November 2026
- Selected enrolment and genuine probe images.
- Used random seed 20261114.
- Recorded image selection counts and checked for duplicates.

### 16 November 2026
- Generated genuine and impostor comparison pairs.
- Used random seed 20261116.
- Selected five impostor references per probe.
- Validated the generated comparison pairs.

### 18 November 2026
- Finalised the simulated home-webcam image degradation design.
- Approved five individual degradation types at three severity levels.
- Approved three combined degradation conditions.
- Frozen random seed 20261118 and degradation parameters.

### 18–19 November 2026
- Generated the pilot degradation dataset.
- Produced 900 degraded images from 50 Development probe images across 18 conditions.
- Inspected degradation contact sheets and approved the visual severity differences.

### 19 November 2026
- Conducted a multiple-face detection diagnostic using MTCNN and YOLOv8n.
- Recorded detection behaviour and identified potential false-positive limitations.

## Upcoming activities

- Generate the complete degradation dataset.
- Validate the full degradation dataset and its manifest.
- Calibrate verification thresholds using Development data.
- Finalise the image-quality gate.
- Implement and evaluate the retry mechanism.
- Calculate final evaluation metrics and statistical comparisons.
- Develop the web-based attendance artefact.
- Document privacy, GDPR and EU AI Act considerations.

---

**Maintenance note:** Add a dated entry whenever a significant research activity is completed. Record actual dates and outcomes, rather than planned activities as completed work.
