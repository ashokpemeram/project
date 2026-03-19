import io
import torch
from PIL import Image
import torchvision.transforms as transforms
from config import IMAGE_SIZE, NORMALIZE_MEAN, NORMALIZE_STD, MAX_FILE_SIZE, allowed_file


def validate_image(file_content: bytes, filename: str) -> tuple[bool, str]:
    """
    Validate uploaded image file
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file extension
    if not allowed_file(filename):
        return False, "Invalid file type. Allowed types: jpg, jpeg, png, bmp, tiff"
    
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
    
    # Try to open as image
    try:
        img = Image.open(io.BytesIO(file_content))
        img.verify()  # Verify it's actually an image
        return True, ""
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


def preprocess_image(image_bytes: bytes, device: str = 'cpu') -> torch.Tensor:
    """
    Preprocess image for model inference
    
    Args:
        image_bytes: Raw image bytes
        device: Device to load tensor on ('cpu' or 'cuda')
        
    Returns:
        Preprocessed image tensor
    """
    # Load image
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Define transforms
    transform = transforms.Compose([
        transforms.Resize(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD)
    ])
    
    # Apply transforms
    img_tensor = transform(img)
    
    # Add batch dimension
    img_tensor = img_tensor.unsqueeze(0)
    
    # Move to device
    img_tensor = img_tensor.to(device)
    
    return img_tensor


def postprocess_output(output_tensor: torch.Tensor) -> bytes:
    """
    Convert model output tensor to image bytes
    
    Args:
        output_tensor: Model output tensor
        
    Returns:
        Image bytes in PNG format
    """
    # Remove batch dimension
    if output_tensor.dim() == 4:
        output_tensor = output_tensor.squeeze(0)
    
    # Move to CPU and convert to numpy
    output_tensor = output_tensor.cpu().detach()
    
    # Denormalize if needed
    # Assuming output is in range [0, 1] or needs denormalization
    if output_tensor.min() < 0:
        # Denormalize using same stats as input
        for t, m, s in zip(output_tensor, NORMALIZE_MEAN, NORMALIZE_STD):
            t.mul_(s).add_(m)
    
    # Clamp values to [0, 1]
    output_tensor = torch.clamp(output_tensor, 0, 1)
    
    # Convert to PIL Image
    transform = transforms.ToPILImage()
    img = transform(output_tensor)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr.getvalue()


def tensor_to_image(tensor: torch.Tensor) -> Image.Image:
    """
    Convert tensor to PIL Image
    
    Args:
        tensor: Image tensor
        
    Returns:
        PIL Image
    """
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)
    
    tensor = tensor.cpu().detach()
    
    # Denormalize if needed
    if tensor.min() < 0:
        for t, m, s in zip(tensor, NORMALIZE_MEAN, NORMALIZE_STD):
            t.mul_(s).add_(m)
    
    tensor = torch.clamp(tensor, 0, 1)
    
    transform = transforms.ToPILImage()
    return transform(tensor)


def output_to_unit_interval(output_tensor: torch.Tensor) -> torch.Tensor:
    """
    Normalize a model output tensor to the [0, 1] range.
    Handles ImageNet-normalized RGB outputs by denormalizing first.
    """
    if output_tensor.dim() == 3:
        output_tensor = output_tensor.unsqueeze(0)
    if output_tensor.dim() != 4:
        raise ValueError(f"Expected output tensor with 3 or 4 dims, got {output_tensor.dim()}.")

    tensor = output_tensor.detach().clone()

    if tensor.min().item() < 0.0:
        if tensor.size(1) == 3:
            for channel, (mean, std) in enumerate(zip(NORMALIZE_MEAN, NORMALIZE_STD)):
                tensor[:, channel].mul_(std).add_(mean)
        elif tensor.size(1) == 1:
            tensor = (tensor + 1.0) / 2.0
        else:
            raise ValueError("Unsupported channel count for denormalization.")

    return tensor.clamp(0.0, 1.0)


def rgb_to_grayscale_minus1_1(rgb_tensor: torch.Tensor) -> torch.Tensor:
    """
    Convert an RGB tensor in [0, 1] to grayscale in [-1, 1].
    """
    if rgb_tensor.dim() == 3:
        rgb_tensor = rgb_tensor.unsqueeze(0)
    if rgb_tensor.dim() != 4:
        raise ValueError(f"Expected RGB tensor with 3 or 4 dims, got {rgb_tensor.dim()}.")

    if rgb_tensor.size(1) == 3:
        r = rgb_tensor[:, 0:1]
        g = rgb_tensor[:, 1:2]
        b = rgb_tensor[:, 2:3]
        gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    elif rgb_tensor.size(1) == 1:
        gray = rgb_tensor
    else:
        raise ValueError("Unsupported channel count for grayscale conversion.")

    gray = gray.clamp(0.0, 1.0)
    return gray * 2.0 - 1.0


def grayscale_minus1_1_to_png_bytes(tensor: torch.Tensor) -> bytes:
    """
    Convert a grayscale tensor in [-1, 1] to PNG bytes.
    """
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)
    if tensor.dim() == 2:
        tensor = tensor.unsqueeze(0)
    if tensor.dim() != 3 or tensor.size(0) != 1:
        raise ValueError("Expected grayscale tensor with shape [1, H, W].")

    tensor = tensor.detach().cpu()
    tensor = ((tensor + 1.0) / 2.0).clamp(0.0, 1.0)
    img = transforms.ToPILImage()(tensor)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


def grayscale_unit_interval_to_png_bytes(tensor: torch.Tensor) -> bytes:
    """
    Convert a grayscale tensor in [0, 1] to PNG bytes.
    """
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)
    if tensor.dim() == 2:
        tensor = tensor.unsqueeze(0)
    if tensor.dim() != 3 or tensor.size(0) != 1:
        raise ValueError("Expected grayscale tensor with shape [1, H, W].")

    tensor = tensor.detach().cpu().clamp(0.0, 1.0)
    img = transforms.ToPILImage()(tensor)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()
