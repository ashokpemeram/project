# System Flow Explanation

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (React Application)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 1. User uploads image
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    IMAGE UPLOADER COMPONENT                     │
│  • Drag & drop support                                          │
│  • File validation (type, size)                                 │
│  • Preview generation                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 2. FormData with image
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LOADING SPINNER                            │
│  • Visual feedback during processing                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 3. HTTP POST request
                         │    (multipart/form-data)
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│                  (app.py - /api/protect-image)                  │
│  • Receives uploaded file                                       │
│  • CORS validation                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 4. File bytes
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION LAYER                             │
│                      (utils.py)                                 │
│  • Check file extension                                         │
│  • Verify file size < 10MB                                      │
│  • Validate image integrity                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 5. Valid image bytes
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PREPROCESSING PIPELINE                         │
│                      (utils.py)                                 │
│  • Load image with PIL                                          │
│  • Convert to RGB                                               │
│  • Resize to model input size (512x512)                         │
│  • Convert to tensor                                            │
│  • Normalize (ImageNet stats)                                   │
│  • Add batch dimension                                          │
│  • Move to device (CPU/GPU)                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 6. Preprocessed tensor
                         │    Shape: [1, 3, 512, 512]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL SERVICE                                │
│                  (model_service.py)                             │
│  • Singleton pattern (load once)                                │
│  • GPU/CPU detection                                            │
│  • Model in eval() mode                                         │
│  • No gradient computation                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 7. Forward pass
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PYTORCH MODEL                                │
│                    (model.pth)                                  │
│  • Deep learning inference                                      │
│  • Image protection/transformation                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 8. Output tensor
                         │    Shape: [1, 3, 512, 512]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 POSTPROCESSING PIPELINE                         │
│                      (utils.py)                                 │
│  • Remove batch dimension                                       │
│  • Move to CPU                                                  │
│  • Denormalize                                                  │
│  • Clamp values [0, 1]                                          │
│  • Convert to PIL Image                                         │
│  • Save as PNG bytes                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 9. PNG image bytes
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI RESPONSE                             │
│  • Content-Type: image/png                                      │
│  • Content-Disposition: attachment                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 10. HTTP Response
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND                               │
│  • Receive blob response                                        │
│  • Create object URL                                            │
│  • Update state                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 11. Display results
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  IMAGE PREVIEW COMPONENT                        │
│  • Side-by-side comparison                                      │
│  • Original vs Protected                                        │
│  • Download button                                              │
│  • Process new image option                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Flow Breakdown

### Phase 1: Frontend Upload (React)

**File: `frontend/src/components/ImageUploader.js`**

1. **User Action:**
   - User drags & drops or selects an image file
   - Triggers `handleFile()` function

2. **Client-Side Validation:**
   ```javascript
   // Check file type
   validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff']
   
   // Check file size
   maxSize = 10MB
   ```

3. **Preview Generation:**
   ```javascript
   URL.createObjectURL(file)  // Create temporary URL for preview
   ```

4. **State Update:**
   ```javascript
   setSelectedImage(file)  // Store file in React state
   ```

### Phase 2: API Request (React → Backend)

**File: `frontend/src/App.js`**

1. **User Clicks "Protect Image":**
   ```javascript
   handleProcess() is called
   ```

2. **Prepare Request:**
   ```javascript
   const formData = new FormData()
   formData.append('image', selectedImage)
   ```

3. **Send HTTP POST:**
   ```javascript
   fetch('http://localhost:5000/api/protect-image', {
     method: 'POST',
     body: formData
   })
   ```

4. **Loading State:**
   ```javascript
   setIsProcessing(true)  // Show loading spinner
   ```

### Phase 3: Backend Reception (FastAPI)

**File: `backend/app.py`**

1. **Endpoint Receives Request:**
   ```python
   @app.post("/api/protect-image")
   async def protect_image(image: UploadFile = File(...))
   ```

2. **Read File Content:**
   ```python
   file_content = await image.read()  # Get raw bytes
   ```

3. **Validate Image:**
   ```python
   is_valid, error_msg = validate_image(file_content, image.filename)
   ```

### Phase 4: Image Preprocessing

**File: `backend/utils.py`**

1. **Load Image:**
   ```python
   img = Image.open(io.BytesIO(image_bytes))
   ```

2. **Convert to RGB:**
   ```python
   if img.mode != 'RGB':
       img = img.convert('RGB')
   ```

3. **Apply Transformations:**
   ```python
   transform = transforms.Compose([
       transforms.Resize((512, 512)),      # Resize
       transforms.ToTensor(),              # Convert to tensor [0, 1]
       transforms.Normalize(               # Normalize
           mean=[0.485, 0.456, 0.406],
           std=[0.229, 0.224, 0.225]
       )
   ])
   ```

4. **Prepare for Model:**
   ```python
   img_tensor = transform(img)           # Apply transforms
   img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension [1, 3, 512, 512]
   img_tensor = img_tensor.to(device)    # Move to GPU/CPU
   ```

### Phase 5: Model Inference

**File: `backend/model_service.py`**

1. **Model Loading (One-time):**
   ```python
   # Singleton pattern - loads only once
   checkpoint = torch.load(MODEL_PATH, map_location=device)
   model.load_state_dict(checkpoint)
   model.eval()  # Set to evaluation mode
   ```

2. **Inference:**
   ```python
   @torch.no_grad()  # Disable gradient computation
   def predict(input_tensor):
       output = self._model(input_tensor)
       return output
   ```

3. **Device Handling:**
   ```python
   if torch.cuda.is_available() and DEVICE == 'cuda':
       device = 'cuda'  # Use GPU
   else:
       device = 'cpu'   # Use CPU
   ```

### Phase 6: Postprocessing

**File: `backend/utils.py`**

1. **Remove Batch Dimension:**
   ```python
   output_tensor = output_tensor.squeeze(0)  # [3, 512, 512]
   ```

2. **Move to CPU:**
   ```python
   output_tensor = output_tensor.cpu().detach()
   ```

3. **Denormalize:**
   ```python
   for t, m, s in zip(output_tensor, NORMALIZE_MEAN, NORMALIZE_STD):
       t.mul_(s).add_(m)  # Reverse normalization
   ```

4. **Clamp Values:**
   ```python
   output_tensor = torch.clamp(output_tensor, 0, 1)
   ```

5. **Convert to Image:**
   ```python
   transform = transforms.ToPILImage()
   img = transform(output_tensor)
   ```

6. **Convert to Bytes:**
   ```python
   img_byte_arr = io.BytesIO()
   img.save(img_byte_arr, format='PNG')
   return img_byte_arr.getvalue()
   ```

### Phase 7: Response & Display

**Backend Response:**
```python
return Response(
    content=output_bytes,
    media_type="image/png",
    headers={"Content-Disposition": "attachment; filename=protected.png"}
)
```

**Frontend Processing:**
```javascript
// Receive blob
const blob = await response.blob()

// Create URL
const imageUrl = URL.createObjectURL(blob)

// Update state
setProtectedImage(imageUrl)

// Display in ImagePreview component
```

---

## 🎯 Key Design Decisions

### 1. **Singleton Pattern for Model**
- Model loads only once on server startup
- Shared across all requests
- Reduces memory usage and latency

### 2. **Async/Await Pattern**
- Non-blocking I/O operations
- Better performance under load
- Handles multiple requests efficiently

### 3. **Client-Side Validation**
- Immediate feedback to user
- Reduces unnecessary server requests
- Better user experience

### 4. **Server-Side Validation**
- Security layer
- Prevents malicious uploads
- Enforces business rules

### 5. **Blob Response**
- Efficient binary transfer
- Direct image download support
- No base64 encoding overhead

---

## 🔧 Configuration Points

### Backend Configuration (`config.py`)
```python
IMAGE_SIZE = (512, 512)           # Model input size
NORMALIZE_MEAN = [0.485, ...]     # Normalization stats
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
DEVICE = 'cpu' or 'cuda'          # Computation device
```

### Frontend Configuration (`.env`)
```env
REACT_APP_API_URL=http://localhost:5000  # Backend URL
```

---

## 📈 Performance Characteristics

- **Model Loading**: ~2-5 seconds (one-time)
- **Image Upload**: ~100-500ms (depends on size)
- **Preprocessing**: ~50-100ms
- **Inference**: ~100-500ms (CPU) / ~10-50ms (GPU)
- **Postprocessing**: ~50-100ms
- **Total**: ~300ms - 1.2s per image

---

## 🛡️ Error Handling

Each layer has error handling:

1. **Frontend**: User-friendly error messages
2. **Validation**: Specific validation errors
3. **Model Service**: Graceful fallback to placeholder
4. **API**: HTTP status codes with details

---

This flow ensures a robust, efficient, and user-friendly medical image protection system!
