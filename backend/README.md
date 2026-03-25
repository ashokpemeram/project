# Secure Hospital Imaging - Backend

FastAPI backend that protects medical images, stores protected outputs, and runs tamper simulations.

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
venv\\Scripts\\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

- Copy `.env.example` to `.env`
- Set `MODEL_PATH` to your weights file
- Set `MODEL_URL` to a public Google Drive link or file ID for first-time downloads
- Set `MODEL_CLASS_PATH` to `model.generator:MitsGanGenerator` or your class

## Model Weights Download

On startup, the backend will download the model to `model/weights/model.pth` if it is missing and `MODEL_URL` is set.
For Render or other ephemeral filesystems, use a persistent disk or expect the model to re-download on each deploy.
Set `ALLOW_PLACEHOLDER_MODEL=1` for dev-only fallback when downloads fail.

## Run

```bash
python app.py
```

The API runs on `http://localhost:10000` by default (or the value of `PORT`).

## Key Endpoints

- POST `/api/auth/signup`
- POST `/api/auth/login`
- POST `/api/upload`
- GET `/api/patients`
- GET `/api/patients/{id}`
- GET `/protected/{filename}`
- POST `/api/attack`

## Notes

- Original images are processed in memory and never stored.
- Only protected images are persisted on disk.
- Attack metrics include MSE, PSNR, and SSIM.

## MongoDB (Optional)

Set `DATA_BACKEND=mongo` in `.env` and configure `MONGO_URI` and `MONGO_DB` to use MongoDB storage. Install dependencies with `pip install -r requirements.txt`.
