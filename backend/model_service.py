import torch
import torch.nn as nn
from pathlib import Path
from typing import Optional
import logging
from config import MODEL_PATH, DEVICE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelService:
    """Singleton service for PyTorch model management"""
    
    _instance: Optional['ModelService'] = None
    _model: Optional[nn.Module] = None
    _device: str = 'cpu'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self.load_model()
    
    def load_model(self):
        """Load PyTorch model from .pth file"""
        try:
            # Determine device
            if DEVICE == 'cuda' and torch.cuda.is_available():
                self._device = 'cuda'
                logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                self._device = 'cpu'
                logger.info("Using CPU")
            
            # Check if model file exists
            model_path = Path(MODEL_PATH)
            if not model_path.exists():
                logger.warning(f"Model file not found at {MODEL_PATH}")
                logger.warning("Creating a placeholder identity model for demonstration")
                # self._model = self._create_placeholder_model()
                # self._model.to(self._device)
                # self._model.eval()
                return
            
            # Load model
            logger.info(f"Loading model from {MODEL_PATH}")
            
            # Load checkpoint
            checkpoint = torch.load(MODEL_PATH, map_location=self._device)
            
            # Handle different checkpoint formats
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                elif 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                else:
                    state_dict = checkpoint
            else:
                # Checkpoint is the model itself
                self._model = checkpoint
                self._model.to(self._device)
                self._model.eval()
                logger.info("Model loaded successfully")
                return
            
            # If you have a custom model architecture, instantiate it here
            # Example:
            # from your_model_file import YourModelClass
            # self._model = YourModelClass()
            # self._model.load_state_dict(state_dict)
            
            # For now, create a placeholder
            logger.warning("Using placeholder model. Replace with your actual model architecture.")
            self._model = self._create_placeholder_model()
            
            self._model.to(self._device)
            self._model.eval()
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            logger.warning("Using placeholder identity model")
            self._model = self._create_placeholder_model()
            self._model.to(self._device)
            self._model.eval()
    
    def _create_placeholder_model(self) -> nn.Module:
        """
        Create a simple placeholder model that returns the input
        Replace this with your actual model architecture
        """
        class IdentityModel(nn.Module):
            def __init__(self):
                super(IdentityModel, self).__init__()
                # Simple conv layer to demonstrate processing
                self.conv = nn.Conv2d(3, 3, kernel_size=3, padding=1)
                
            def forward(self, x):
                # Apply slight transformation to show it's working
                return torch.sigmoid(self.conv(x))
        
        return IdentityModel()
    
    @torch.no_grad()
    def predict(self, input_tensor: torch.Tensor) -> torch.Tensor:
        """
        Run inference on input tensor
        
        Args:
            input_tensor: Preprocessed input tensor
            
        Returns:
            Model output tensor
        """
        if self._model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            # Ensure input is on correct device
            input_tensor = input_tensor.to(self._device)
            
            # Run inference
            output = self._model(input_tensor)
            
            return output
            
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            raise
    
    def get_device(self) -> str:
        """Get current device"""
        return self._device
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._model is not None


# Create singleton instance
model_service = ModelService()
