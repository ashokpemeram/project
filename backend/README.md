# Medical Image Protection - Backend

Backend API for processing medical images using PyTorch models.

## Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Update `MODEL_PATH` to point to your `.pth` file
   - Set `DEVICE` to `cuda` if you have GPU support

4. **Add your model:**
   - Place your trained `.pth` model file in the `models/` directory
   - Update `model_service.py` if you have a custom model architecture

## Running the Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /api/health
```

### Process Image
```
POST /api/protect-image
Content-Type: multipart/form-data
Body: image (file)

Returns: Protected image (PNG)
```

### Process Image (JSON Response)
```
POST /api/protect-image-json
Content-Type: multipart/form-data
Body: image (file)

Returns: JSON with base64 encoded image
```

## Testing

Test with curl:
```bash
curl -X POST http://localhost:5000/api/protect-image \
  -F "image=@path/to/your/image.jpg" \
  --output protected_image.png
```

## Project Structure

```
backend/
├── app.py              # FastAPI application
├── model_service.py    # PyTorch model management
├── utils.py           # Image processing utilities
├── config.py          # Configuration settings
├── requirements.txt   # Python dependencies
├── models/           # Model files (.pth)
└── uploads/          # Temporary upload directory
```

## Notes

- The current implementation includes a placeholder model for demonstration
- Replace the placeholder in `model_service.py` with your actual model architecture
- Adjust `IMAGE_SIZE`, `NORMALIZE_MEAN`, and `NORMALIZE_STD` in `config.py` based on your model requirements
