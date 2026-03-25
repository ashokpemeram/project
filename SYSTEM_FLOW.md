# Secure Hospital Imaging System Flow

## Architecture

Frontend (React) -> Backend API (FastAPI) -> Model Service (PyTorch) -> Storage (Protected images + JSON metadata)

## Data Flow

1. Doctor uploads scan + patient details
2. Backend validates file and runs generator
3. Protected image is stored (original discarded)
4. Patient record is persisted in JSON storage
5. Doctor retrieves record and launches tamper simulation
6. Backend applies attack, computes metrics, returns maps

## Core Endpoints

- POST /api/auth/signup
- POST /api/auth/login
- POST /api/upload
- GET /api/patients
- GET /api/patients/{id}
- GET /protected/{filename}
- POST /api/attack

## Demo Script

1. Sign up and log in
2. Upload a CT or X-ray scan with metadata
3. Confirm protected image appears in Patient Records
4. Open Tamper Simulation and choose the patient
5. Run Noise, Patch, Cutout, and Combined attacks
6. Review MSE, PSNR, SSIM with heatmap and mask
