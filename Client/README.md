# Medical Image Protection - Frontend

React-based frontend for the Medical Image Protection System.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   - The `.env` file is already configured to connect to `http://localhost:5000`
   - Update `REACT_APP_API_URL` if your backend runs on a different port

## Running the Application

```bash
npm start
```

The application will open at `http://localhost:3000`

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Features

- **Drag & Drop Upload**: Intuitive file upload with drag-and-drop support
- **Image Preview**: Preview selected images before processing
- **Real-time Processing**: Live feedback during image processing
- **Side-by-Side Comparison**: Compare original and protected images
- **Download Protected Images**: Easy download of processed images
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Error Handling**: Clear error messages for better user experience

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── ImageUploader.js      # Upload component
│   │   ├── ImageUploader.css
│   │   ├── ImagePreview.js       # Results display
│   │   ├── ImagePreview.css
│   │   ├── LoadingSpinner.js     # Loading indicator
│   │   └── LoadingSpinner.css
│   ├── App.js                    # Main application
│   ├── App.css                   # Global styles
│   └── index.js                  # Entry point
└── package.json
```

## Supported File Types

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)

Maximum file size: 10MB

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Troubleshooting

### Backend Connection Issues

If you see connection errors:
1. Ensure the backend server is running on `http://localhost:5000`
2. Check that CORS is properly configured in the backend
3. Verify the `REACT_APP_API_URL` in `.env` is correct

### Image Upload Issues

If images fail to upload:
1. Check file size (must be < 10MB)
2. Verify file format is supported
3. Check browser console for detailed error messages
