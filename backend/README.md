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
- Set `MODEL_CLASS_PATH` to `model.generator:MitsGanGenerator` or your class

## Run

```bash
python app.py
```

The API runs on `http://localhost:5000`.

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
