"""Filmstrip Grid Generator Module

This module handles the arrangement of images into an n×n grid layout,
optimizing for WebP resolution utilization.
"""

import math
from pathlib import Path
from typing import List, Union, Tuple, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class FilmstripGenerator:
    """Generates n×n grid filmstrip from a collection of images."""
    
    def __init__(self, background_color: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        """
        Initialize the filmstrip generator.
        
        Args:
            background_color: RGBA color for empty cells, default is transparent black
        """
        self.background_color = background_color
    
    @staticmethod
    def calculate_grid_size(num_images: int) -> int:
        """
        Calculate optimal n×n grid size for given number of images.
        
        Args:
            num_images: Number of images to arrange
            
        Returns:
            Grid size (n) where n*n >= num_images
            
        Examples:
            9 images -> 3x3 grid
            10 images -> 4x4 grid (6 empty cells)
            16 images -> 4x4 grid
        """
        if num_images <= 0:
            return 0
        return math.ceil(math.sqrt(num_images))
    
    def get_max_dimensions(self, image_paths: List[Path]) -> Tuple[int, int]:
        """
        Get the maximum width and height from a list of images.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Tuple of (max_width, max_height)
        """
        max_width = 0
        max_height = 0
        
        for img_path in image_paths:
            try:
                with Image.open(img_path) as img:
                    max_width = max(max_width, img.width)
                    max_height = max(max_height, img.height)
            except Exception as e:
                logger.warning(f"Could not read {img_path}: {str(e)}")
                continue
        
        return max_width, max_height
    
    def create_filmstrip(self, image_paths: List[Union[str, Path]], 
                        output_dir: Union[str, Path],
                        name: str = "filmstrip",
                        grid_size: Optional[int] = None,
                        quality: int = 90) -> Path:
        """
        Create an n×n grid filmstrip from a list of images.
        
        Args:
            image_paths: List of image file paths to include in filmstrip
            output_dir: Directory path for the output filmstrip WebP file
            name: Base name for the output file
            grid_size: Override automatic grid size calculation (optional)
            quality: WebP quality setting (0-100)
            
        Returns:
            Path to the created filmstrip file
            
        Raises:
            ValueError: If no valid images provided or invalid grid size
        """
        if not image_paths:
            raise ValueError("No image paths provided")
        
        # Convert to Path objects
        image_paths = [Path(p) for p in image_paths]
        output_dir = Path(output_dir)
        
        # Filter out non-existent files
        valid_images = [p for p in image_paths if p.exists()]
        if not valid_images:
            raise ValueError("No valid image files found")
        
        num_images = len(valid_images)
        logger.info(f"Creating filmstrip from {num_images} images")
        
        # Calculate or validate grid size
        if grid_size is None:
            grid_size = self.calculate_grid_size(num_images)
        else:
            if grid_size < self.calculate_grid_size(num_images):
                raise ValueError(
                    f"Grid size {grid_size}x{grid_size} too small for {num_images} images"
                )
        
        logger.info(f"Using {grid_size}x{grid_size} grid")
        
        # Get maximum dimensions for uniform cell sizing
        cell_width, cell_height = self.get_max_dimensions(valid_images)
        
        if cell_width == 0 or cell_height == 0:
            raise ValueError("Could not determine valid image dimensions")
        
        # Create the filmstrip canvas
        filmstrip_width = cell_width * grid_size
        filmstrip_height = cell_height * grid_size
        
        # Use RGBA mode to support transparency
        filmstrip = Image.new('RGBA', (filmstrip_width, filmstrip_height), 
                             self.background_color)
        
        # Place images in grid
        for idx, img_path in enumerate(valid_images):
            if idx >= grid_size * grid_size:
                logger.warning(f"Skipping image {idx + 1}, grid is full")
                break
            
            # Calculate grid position (left to right, top to bottom)
            row = idx // grid_size
            col = idx % grid_size
            
            # Calculate paste position
            x = col * cell_width
            y = row * cell_height
            
            try:
                with Image.open(img_path) as img:
                    # Convert to RGBA if needed
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # Center the image in the cell if it's smaller
                    offset_x = (cell_width - img.width) // 2
                    offset_y = (cell_height - img.height) // 2
                    
                    filmstrip.paste(img, (x + offset_x, y + offset_y), img)
                    logger.debug(f"Placed {img_path.name} at position ({row}, {col})")
                    
            except Exception as e:
                logger.error(f"Failed to add {img_path.name} to filmstrip: {str(e)}")
                continue
        
        # Construct filename: [name]_[FrameSize]_[TotalFrames]_[GridWidth]x[GridHeight].webp
        # FrameSize is typically WxH of a single frame
        filename = f"{name}_{cell_width}x{cell_height}_{num_images}_{grid_size}x{grid_size}.webp"
        output_path = output_dir / filename

        # Save as WebP
        output_path.parent.mkdir(parents=True, exist_ok=True)
        filmstrip.save(output_path, 'WEBP', quality=quality)
        
        logger.info(f"Filmstrip saved to {output_path}")
        logger.info(f"Final dimensions: {filmstrip_width}x{filmstrip_height}px")
        
        return output_path
    
    def create_filmstrip_from_dir(self, input_dir: Union[str, Path],
                                  output_path: Union[str, Path],
                                  grid_size: Optional[int] = None,
                                  quality: int = 90,
                                  pattern: str = '*.*') -> Path:
        """
        Create filmstrip from all images in a directory.
        
        Args:
            input_dir: Directory containing images
            output_path: Path for output filmstrip
            grid_size: Override automatic grid size (optional)
            quality: WebP quality setting
            pattern: Glob pattern for finding images (default: *.*)
            
        Returns:
            Path to created filmstrip
        """
        input_dir = Path(input_dir)
        
        if not input_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {input_dir}")
        
        # Find all image files
        image_files = sorted(input_dir.glob(pattern))
        
        # Filter for common image formats
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}
        image_files = [f for f in image_files 
                      if f.suffix.lower() in valid_extensions]
        
        if not image_files:
            raise ValueError(f"No image files found in {input_dir}")
        
        logger.info(f"Found {len(image_files)} images in {input_dir}")
        
        return self.create_filmstrip(image_files, output_path, name=input_dir.name, grid_size=grid_size, quality=quality)
