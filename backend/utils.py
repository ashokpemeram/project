import io
import torch
from PIL import Image
import torchvision.transforms as transforms

from config import (
    IMAGE_SIZE,
    NORMALIZE_MEAN,
    NORMALIZE_STD,
    MAX_FILE_SIZE,
    MODEL_INPUT_CHANNELS,
    MODEL_INPUT_RANGE,
    allowed_file,
)


def validate_image(file_content: bytes, filename: str) -> tuple[bool, str]:
    if not allowed_file(filename):
        return False, "Invalid file type. Allowed types: jpg, jpeg, png, bmp, tiff"

    if len(file_content) > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"

    try:
        img = Image.open(io.BytesIO(file_content))
        img.verify()
        return True, ""
    except Exception as exc:
        return False, f"Invalid image file: {str(exc)}"


def preprocess_image(image_bytes: bytes, device: str = "cpu") -> torch.Tensor:
    img = Image.open(io.BytesIO(image_bytes))

    if MODEL_INPUT_CHANNELS == 1:
        img = img.convert("L")
    else:
        img = img.convert("RGB")

    transform = transforms.Compose(
        [
            transforms.Resize(IMAGE_SIZE),
            transforms.ToTensor(),
        ]
    )

    img_tensor = transform(img)

    if MODEL_INPUT_RANGE == "tanh":
        img_tensor = img_tensor * 2.0 - 1.0
    elif MODEL_INPUT_RANGE == "imagenet":
        if img_tensor.size(0) == 3:
            img_tensor = transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD)(img_tensor)
    elif MODEL_INPUT_RANGE != "unit":
        raise ValueError(f"Unsupported MODEL_INPUT_RANGE: {MODEL_INPUT_RANGE}")

    img_tensor = img_tensor.unsqueeze(0)
    img_tensor = img_tensor.to(device)

    return img_tensor


def load_image_unit_tensor(
    image_bytes: bytes,
    device: str = "cpu",
    size: tuple[int, int] | None = IMAGE_SIZE,
) -> torch.Tensor:
    img = Image.open(io.BytesIO(image_bytes))
    if MODEL_INPUT_CHANNELS == 1:
        img = img.convert("L")
    else:
        img = img.convert("RGB")
    if size is not None:
        img = img.resize(size)

    transform = transforms.ToTensor()
    img_tensor = transform(img)
    img_tensor = img_tensor.unsqueeze(0)
    img_tensor = img_tensor.to(device)
    return img_tensor


def _denormalize_tensor(tensor: torch.Tensor) -> torch.Tensor:
    if tensor.size(0) == 1:
        return (tensor + 1.0) / 2.0
    if tensor.size(0) == 3:
        for t, m, s in zip(tensor, NORMALIZE_MEAN, NORMALIZE_STD):
            t.mul_(s).add_(m)
        return tensor
    raise ValueError("Unsupported channel count for denormalization.")


def postprocess_output(output_tensor: torch.Tensor) -> bytes:
    if output_tensor.dim() == 4:
        output_tensor = output_tensor.squeeze(0)

    output_tensor = output_tensor.cpu().detach()

    if output_tensor.min() < 0:
        output_tensor = _denormalize_tensor(output_tensor)

    output_tensor = torch.clamp(output_tensor, 0, 1)

    transform = transforms.ToPILImage()
    img = transform(output_tensor)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue()


def tensor_to_image(tensor: torch.Tensor) -> Image.Image:
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)

    tensor = tensor.cpu().detach()

    if tensor.min() < 0:
        tensor = _denormalize_tensor(tensor)

    tensor = torch.clamp(tensor, 0, 1)

    transform = transforms.ToPILImage()
    return transform(tensor)


def output_to_unit_interval(output_tensor: torch.Tensor) -> torch.Tensor:
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
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


def grayscale_unit_interval_to_png_bytes(tensor: torch.Tensor) -> bytes:
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)
    if tensor.dim() == 2:
        tensor = tensor.unsqueeze(0)
    if tensor.dim() != 3 or tensor.size(0) != 1:
        raise ValueError("Expected grayscale tensor with shape [1, H, W].")

    tensor = tensor.detach().cpu().clamp(0.0, 1.0)
    img = transforms.ToPILImage()(tensor)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()
