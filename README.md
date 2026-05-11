# Secure Hospital Management Imaging System

A full-stack demo that protects medical scans with a PyTorch generator, stores only protected images, and simulates tampering attacks for analysis.

## Architecture

- **frontend/** React doctor console with login, dashboard, patient records, and tamper simulation.
- **backend/** FastAPI service for auth, upload/protection, patient records, and attack simulation.
- **model/** Generator class definition and model weights.
- **attacker/** Attack operators and metrics (MSE, PSNR, SSIM).

Data flow: Doctor upload -> protection -> protected storage -> retrieval -> attack simulation -> analysis results.

## Security Note

Original images are processed in memory and never stored. Only protected images are persisted. This system ensures integrity of medical images against AI-based tampering attacks.

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Demo Flow

1. Admin signs in and creates a doctor account.
2. Doctor logs in with the provided credentials.
3. Upload a patient scan with metadata.
4. System generates the protected image and stores it.
5. Review patient record.
6. Open tamper simulation.
7. Run attacks and review the metrics and masks.

## Database

This demo can use MongoDB. Set `DATA_BACKEND=mongo` and configure `MONGO_URI` and `MONGO_DB` in `backend/.env`.
