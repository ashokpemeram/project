import React, { useState, useRef } from 'react';
import './ImageUploader.css';

const ImageUploader = ({
  onImageSelect,
  selectedImage,
  onClear,
  onProcess,
  isProcessing,
  attackEnabled,
  attackType,
  onAttackToggle,
  onAttackTypeChange,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'];
    if (!validTypes.includes(file.type)) {
      alert('Please upload a valid image file (JPG, PNG, BMP, or TIFF)');
      return;
    }

    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('File size must be less than 10MB');
      return;
    }

    onImageSelect(file);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div>
      {!selectedImage ? (
        <div
          className={`image-uploader ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={handleButtonClick}
        >
          <div className="upload-icon">📁</div>
          <div className="upload-text">
            {dragActive ? 'Drop your image here' : 'Drag & Drop your medical image'}
          </div>
          <div className="upload-subtext">or</div>
          <button className="upload-button" type="button">
            <span>Browse Files</span>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            className="file-input"
            accept="image/jpeg,image/jpg,image/png,image/bmp,image/tiff"
            onChange={handleChange}
          />
          <div className="upload-subtext" style={{ marginTop: '1rem' }}>
            Supported formats: JPG, PNG, BMP, TIFF (Max 10MB)
          </div>
        </div>
      ) : (
        <div className="preview-container">
          <div className="preview-header">
            <h3 className="preview-title">Selected Image</h3>
            <button className="clear-button" onClick={onClear}>
              ✕ Clear
            </button>
          </div>
          <img
            src={URL.createObjectURL(selectedImage)}
            alt="Selected"
            className="preview-image"
          />
          <div className="file-info">
            <div className="file-info-item">
              <span className="file-info-label">File name:</span>
              <span>{selectedImage.name}</span>
            </div>
            <div className="file-info-item">
              <span className="file-info-label">File size:</span>
              <span>{formatFileSize(selectedImage.size)}</span>
            </div>
            <div className="file-info-item">
              <span className="file-info-label">File type:</span>
              <span>{selectedImage.type}</span>
            </div>
          </div>
          <div className="attack-options">
            <label className="attack-toggle">
              <input
                type="checkbox"
                checked={attackEnabled}
                onChange={(e) => onAttackToggle(e.target.checked)}
                disabled={isProcessing}
              />
              <span>Simulate attacker on protected image</span>
            </label>
            {attackEnabled && (
              <div className="attack-select">
                <span className="attack-label">Attack type</span>
                <select
                  value={attackType}
                  onChange={(e) => onAttackTypeChange(e.target.value)}
                  disabled={isProcessing}
                >
                  <option value="combined">Combined (recommended)</option>
                  <option value="noise">Gaussian noise</option>
                  <option value="blur">Blur</option>
                  <option value="patch">Patch</option>
                  <option value="cutout">Cutout</option>
                </select>
              </div>
            )}
          </div>
          <button
            className="process-button"
            onClick={onProcess}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <>
                <span className="spinner">⏳</span>
                <span>Processing...</span>
              </>
            ) : (
              <>
                <span>🔒</span>
                <span>Protect Image</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default ImageUploader;
