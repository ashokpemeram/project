import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ message = 'Processing your image...', subtext = 'This may take a few moments' }) => {
    return (
        <div className="loading-spinner">
            <div className="spinner"></div>
            <div className="loading-text">{message}</div>
            <div className="loading-subtext">{subtext}</div>
            <div className="progress-bar-container">
                <div className="progress-bar"></div>
            </div>
        </div>
    );
};

export default LoadingSpinner;
