import React from 'react';
import './ImagePreview.css';

const ImagePreview = ({
    originalImage,
    protectedImage,
    attackedImage,
    tamperMap,
    tamperMask,
    attackMetrics,
    onNewImage,
}) => {
    const formatMetric = (value, digits) => {
        if (value === null || value === undefined) return '—';
        const numeric = Number(value);
        if (Number.isNaN(numeric)) return '—';
        return numeric.toFixed(digits);
    };

    const handleDownload = (imageUrl, label) => {
        if (!imageUrl) return;
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = `${label}_${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="image-preview">
            <div className="preview-header">
                <h2>âœ… Image Protected Successfully!</h2>
                <p>Your medical image has been processed and secured</p>
            </div>

            <div className="images-container">
                <div className="image-card">
                    <div className="image-card-header">
                        <span className="image-card-icon">ðŸ“·</span>
                        <h3 className="image-card-title">Original Image</h3>
                    </div>
                    <div className="image-wrapper">
                        <img src={originalImage} alt="Original" />
                        <div className="image-badge">Original</div>
                    </div>
                </div>

                <div className="image-card">
                    <div className="image-card-header">
                        <span className="image-card-icon">ðŸ”’</span>
                        <h3 className="image-card-title">Protected Image</h3>
                    </div>
                    <div className="image-wrapper">
                        <img src={protectedImage} alt="Protected" />
                        <div className="image-badge">Protected</div>
                    </div>
                </div>

                {attackedImage && (
                    <div className="image-card attacked-card">
                        <div className="image-card-header">
                            <span className="image-card-icon">ðŸš¨</span>
                            <h3 className="image-card-title">Attacked Image</h3>
                        </div>
                        <div className="image-wrapper">
                            <img src={attackedImage} alt="Attacked" />
                            <div className="image-badge warning-badge">Attacked</div>
                        </div>
                    </div>
                )}
                {tamperMap && (
                    <div className="image-card tamper-card">
                        <div className="image-card-header">
                            <span className="image-card-icon">!</span>
                            <h3 className="image-card-title">Tamper Map</h3>
                        </div>
                        <div className="image-wrapper">
                            <img src={tamperMap} alt="Tamper map" />
                            <div className="image-badge warning-badge">Heatmap</div>
                        </div>
                    </div>
                )}
                {tamperMask && (
                    <div className="image-card tamper-card">
                        <div className="image-card-header">
                            <span className="image-card-icon">#</span>
                            <h3 className="image-card-title">Tamper Mask</h3>
                        </div>
                        <div className="image-wrapper">
                            <img src={tamperMask} alt="Tamper mask" />
                            <div className="image-badge warning-badge">Mask</div>
                        </div>
                    </div>
                )}
            </div>

            {attackMetrics && (
                <div className="attack-metrics">
                    <h4>Attack Metrics</h4>
                    <div className="metrics-grid">
                        <div className="metric-card">
                            <span className="metric-label">MSE (protected vs original)</span>
                            <span className="metric-value">
                                {formatMetric(attackMetrics.mse_protected_vs_original, 4)}
                            </span>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">PSNR (protected vs original)</span>
                            <span className="metric-value">
                                {formatMetric(attackMetrics.psnr_protected_vs_original, 2)}
                            </span>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Attack distance</span>
                            <span className="metric-value">
                                {formatMetric(attackMetrics.attack_distance, 4)}
                            </span>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">MSE (attacked vs protected)</span>
                            <span className="metric-value">
                                {formatMetric(attackMetrics.mse_attacked_vs_protected, 4)}
                            </span>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">PSNR (attacked vs protected)</span>
                            <span className="metric-value">
                                {formatMetric(attackMetrics.psnr_attacked_vs_protected, 2)}
                            </span>
                        </div>
                    </div>
                </div>
            )}

            <div className="actions-container">
                <button
                    className="action-button download-button"
                    onClick={() => handleDownload(protectedImage, 'protected')}
                >
                    <span>â¬‡ï¸</span>
                    <span>Download Protected Image</span>
                </button>
                {attackedImage && (
                    <button
                        className="action-button attack-download-button"
                        onClick={() => handleDownload(attackedImage, 'attacked')}
                    >
                        <span>âš¡</span>
                        <span>Download Attacked Image</span>
                    </button>
                )}
                <button className="action-button new-image-button" onClick={onNewImage}>
                    <span>ðŸ”„</span>
                    <span>Process New Image</span>
                </button>
            </div>
        </div>
    );
};

export default ImagePreview;
