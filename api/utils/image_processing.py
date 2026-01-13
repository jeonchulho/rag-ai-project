"""Image processing utilities."""

import logging
from typing import Tuple
from PIL import Image
import io

logger = logging.getLogger(__name__)


def resize_image(
    image_data: bytes,
    max_width: int = 1024,
    max_height: int = 1024
) -> bytes:
    """
    Resize image to fit within maximum dimensions.
    
    Args:
        image_data: Image data as bytes
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized image data as bytes
    """
    try:
        # Open image
        img = Image.open(io.BytesIO(image_data))
        
        # Calculate new size maintaining aspect ratio
        ratio = min(max_width / img.width, max_height / img.height)
        if ratio < 1:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format=img.format or 'PNG')
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Image resize failed: {e}")
        return image_data


def get_image_dimensions(image_data: bytes) -> Tuple[int, int]:
    """
    Get image dimensions.
    
    Args:
        image_data: Image data as bytes
        
    Returns:
        Tuple of (width, height)
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        return img.size
    except Exception as e:
        logger.error(f"Failed to get image dimensions: {e}")
        return (0, 0)


def convert_to_rgb(image_data: bytes) -> bytes:
    """
    Convert image to RGB format.
    
    Args:
        image_data: Image data as bytes
        
    Returns:
        RGB image data as bytes
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        output = io.BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Image conversion failed: {e}")
        return image_data


def validate_image(image_data: bytes) -> bool:
    """
    Validate that data is a valid image.
    
    Args:
        image_data: Image data as bytes
        
    Returns:
        True if valid image, False otherwise
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        img.verify()
        return True
    except Exception:
        return False
