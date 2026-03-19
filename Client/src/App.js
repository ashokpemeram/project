import React, { useState } from 'react';
import './App.css';
import ImageUploader from './components/ImageUploader';
import ImagePreview from './components/ImagePreview';
import LoadingSpinner from './components/LoadingSpinner';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [protectedImage, setProtectedImage] = useState(null);
  const [attackedImage, setAttackedImage] = useState(null);
  const [tamperMap, setTamperMap] = useState(null);
  const [tamperMask, setTamperMask] = useState(null);
  const [attackMetrics, setAttackMetrics] = useState(null);
  const [attackEnabled, setAttackEnabled] = useState(false);
  const [attackType, setAttackType] = useState('combined');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleImageSelect = (file) => {
    setSelectedImage(file);
    setProtectedImage(null);
    setAttackedImage(null);
    setTamperMap(null);
    setTamperMask(null);
    setAttackMetrics(null);
    setError(null);
  };

  const handleClear = () => {
    setSelectedImage(null);
    setProtectedImage(null);
    setAttackedImage(null);
    setTamperMap(null);
    setTamperMask(null);
    setAttackMetrics(null);
    setError(null);
  };

  const handleProcess = async () => {
    if (!selectedImage) return;

    setIsProcessing(true);
    setError(null);

    try {
      // Create form data
      const formData = new FormData();
      formData.append('image', selectedImage);

      if (attackEnabled) {
        formData.append('attack_type', attackType);

        const response = await fetch(`${API_URL}/api/protect-image-attack`, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok || !data.success) {
          throw new Error(data.error || data.detail || `Server error: ${response.status}`);
        }

        setProtectedImage(data.protected_image);
        setAttackedImage(data.attacked_image);
        setTamperMap(data.tamper_map || null);
        setTamperMask(data.tamper_mask || null);
        setAttackMetrics(data.metrics || null);
      } else {
        // Send request to backend
        const response = await fetch(`${API_URL}/api/protect-image`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Server error: ${response.status}`);
        }

        // Get the protected image as blob
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);

        setProtectedImage(imageUrl);
        setAttackedImage(null);
        setTamperMap(null);
        setTamperMask(null);
        setAttackMetrics(null);
      }
    } catch (err) {
      console.error('Error processing image:', err);
      setError(err.message || 'Failed to process image. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleNewImage = () => {
    setSelectedImage(null);
    setProtectedImage(null);
    setAttackedImage(null);
    setTamperMap(null);
    setTamperMask(null);
    setAttackMetrics(null);
    setError(null);
  };

  const handleAttackToggle = (enabled) => {
    setAttackEnabled(enabled);
    if (!enabled) {
      setAttackedImage(null);
      setTamperMap(null);
      setTamperMask(null);
      setAttackMetrics(null);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">🏥 Medical Image Protection System</h1>
        <p className="app-subtitle">
          Secure your medical images with AI-powered protection
        </p>
      </header>

      <main className="main-container">
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <div>
              <strong>Error:</strong> {error}
            </div>
          </div>
        )}

        {isProcessing ? (
          <LoadingSpinner
            message="Processing your image..."
            subtext="Applying AI-powered protection to your medical image"
          />
        ) : protectedImage ? (
          <ImagePreview
            originalImage={URL.createObjectURL(selectedImage)}
            protectedImage={protectedImage}
            attackedImage={attackedImage}
            tamperMap={tamperMap}
            tamperMask={tamperMask}
            attackMetrics={attackMetrics}
            onNewImage={handleNewImage}
          />
        ) : (
          <ImageUploader
            onImageSelect={handleImageSelect}
            selectedImage={selectedImage}
            onClear={handleClear}
            onProcess={handleProcess}
            isProcessing={isProcessing}
            attackEnabled={attackEnabled}
            attackType={attackType}
            onAttackToggle={handleAttackToggle}
            onAttackTypeChange={setAttackType}
          />
        )}
      </main>

      <footer style={{
        textAlign: 'center',
        marginTop: '2rem',
        color: 'rgba(255, 255, 255, 0.8)',
        fontSize: '0.875rem'
      }}>
        <p>Powered by PyTorch & React | Medical Image Protection v1.0</p>
      </footer>
    </div>
  );
}

export default App;
