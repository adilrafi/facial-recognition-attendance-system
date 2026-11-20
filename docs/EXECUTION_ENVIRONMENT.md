# Execution Environment and File Paths

## 1. Development Environment

The research preparation scripts were developed and executed on a Windows 11 computer.

The environment included:

- **Operating system:** Windows 11
- **Shell:** Windows PowerShell 5.1
- **Programming languages:** Python and PowerShell
- **Version control:** Git
- **Repository hosting:** GitHub

Python scripts were executed using dedicated virtual environments where required. Different environments were maintained for specific technical dependencies and experimental tasks.

## 2. Project Directory Structure

The project was organised into separate directories for source code, research preparation, datasets and experimental outputs.

The main directories included:

- `Scripts/` – research preparation and experimental scripts.
- `methodology_preparation/` – local research preparation files, manifests, experimental data and generated outputs.
- `docs/` – project documentation.
- `test_detector_inference.py`, `test_model_input_shapes.py` and `test_pipeline_verification.py` – local technical testing scripts.

## 3. File Paths and Portability

During development, some scripts used absolute local file paths based on the directory structure of the researcher's computer.

These paths reflect the actual environment used to conduct the experiments and generate the research outputs.

Researchers or developers wishing to execute these scripts on another computer should review and update the relevant input and output paths within each script to match their local directory structure before execution.

Project-relative paths were used where appropriate to locate files within the repository.

## 4. Dataset and Experimental Output Management

The original Labeled Faces in the Wild (LFW) dataset was maintained locally and was not included in the public GitHub repository.

Generated degradation images, identity-level manifests, comparison-pair files, annotated face images and other experimental outputs were also maintained locally.

These files have been kept locally and have not been committed to the public GitHub repository. This approach avoids publishing large datasets, identity-level information and experimental outputs unnecessarily.

The repository therefore preserves the research preparation code and documentation rather than the complete local experimental dataset.

## 5. Reproducibility Considerations

Where applicable, scripts use fixed random seeds to support reproducibility of sampling, data selection and experimental preparation.

Reproducing the experiments requires access to the appropriate original dataset, compatible software dependencies, the required local directory structure and the relevant input files.

The Python packages and versions used for individual experimental environments should be recorded alongside the methodology and technical implementation documentation.
