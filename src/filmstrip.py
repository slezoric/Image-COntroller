"""Filmstrip Grid Generator Module

This module handles the arrangement of images into an n×n grid layout,
optimizing for WebP resolution utilization.
"""

import math
import re
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
    def natural_sort_key(s):
        """
        Key for natural sorting (e.g., img2 before img10).
        Splits string into text and numbers.
        """
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split('([0-9]+)', str(s))]

    @staticmethod
    def calculate_optimal_dimensions(num_images: int) -> Tuple[int, int]:
        """
        Calculate optimal grid dimensions (cols, rows) for given number of images.
        Minimizes empty cells.
        
        Args:
            num_images: Number of images to arrange
            
        Returns:
            Tuple of (cols, rows)
            
        Examples:
            9 images -> (3, 3)
            5 images -> (3, 2)  (previously 3x3)
            10 images -> (4, 3) (previously 4x4)
        """
        if num_images <= 0:
            return 0, 0
            
        # Try to make it somewhat square, but prefer wider if needed
        cols = math.ceil(math.sqrt(num_images))
        rows = math.ceil(num_images / cols)
        
        return cols, rows

    @staticmethod
    def calculate_grid_size(num_images: int) -> int:
        """
        Calculate square grid size. Retained for backward compatibility/manual override logic.
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
                        quality: int = 90,
                        autocrop: bool = False,
                        save_format: str = 'WEBP') -> Path:
        """
        Create a grid filmstrip from a list of images.
        
        Args:
            image_paths: List of image file paths to include in filmstrip
            output_dir: Directory path for the output filmstrip WebP file
            name: Base name for the output file
            grid_size: Override automatic grid size calculation (n for n×n) (optional)
            quality: WebP quality setting (0-100)
            autocrop: If True, crop images to their visible content
            save_format: Output format ('WEBP' or 'PNG')
            
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
        
        # Calculate grid dimensions
        if grid_size is None:
            cols, rows = self.calculate_optimal_dimensions(num_images)
        else:
            # Manual square override
            min_size = self.calculate_grid_size(num_images)
            if grid_size < min_size:
                raise ValueError(
                    f"Grid size {grid_size}x{grid_size} too small for {num_images} images"
                )
            cols = grid_size
            rows = grid_size
        
        # Sanitize name (replace spaces with hyphens)
        name = name.replace(' ', '-')
        
        logger.info(f"Using {cols}x{rows} grid")
        
        # Calculate dimensions
        image_bboxes = {}  # Store calculated bboxes if autocrop is True
        
        if autocrop:
            logger.info("Calculating optimal crop bounds...")
            max_width = 0
            max_height = 0
            
            for img_path in valid_images:
                try:
                    with Image.open(img_path) as img:
                        bbox = img.getbbox()
                        if bbox:
                            # bbox is (left, upper, right, lower)
                            w = bbox[2] - bbox[0]
                            h = bbox[3] - bbox[1]
                            image_bboxes[img_path] = bbox
                            max_width = max(max_width, w)
                            max_height = max(max_height, h)
                        else:
                            # Empty/fully transparent image
                            image_bboxes[img_path] = None
                except Exception as e:
                    logger.warning(f"Could not read {img_path}: {str(e)}")
            
            cell_width, cell_height = max_width, max_height
            logger.info(f"Autocrop enabled. content size: {cell_width}x{cell_height}")
            
        else:
            # Get maximum dimensions for uniform cell sizing (original size)
            cell_width, cell_height = self.get_max_dimensions(valid_images)
        
        if cell_width == 0 or cell_height == 0:
             # Fallback if all images are empty or errors
            logger.warning("Dimensions were 0, defaulting to 1x1")
            cell_width, cell_height = 1, 1
        
        # Create the filmstrip canvas
        filmstrip_width = cell_width * cols
        filmstrip_height = cell_height * rows
        
        # Use RGBA mode to support transparency
        filmstrip = Image.new('RGBA', (filmstrip_width, filmstrip_height), 
                             self.background_color)
        
        # Place images in grid
        for idx, img_path in enumerate(valid_images):
            if idx >= cols * rows:
                logger.warning(f"Skipping image {idx + 1}, grid is full")
                break
            
            # Calculate grid position (left to right, top to bottom)
            row = idx // cols
            col = idx % cols
            
            # Calculate paste position
            x = col * cell_width
            y = row * cell_height
            
            try:
                with Image.open(img_path) as img:
                    # Convert to RGBA if needed
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    current_img = img
                    
                    # Apply autocrop if enabled
                    if autocrop:
                        bbox = image_bboxes.get(img_path)
                        if bbox:
                            current_img = img.crop(bbox)
                        else:
                            # Empty image, nothing to paste
                            continue
                    
                    # Center the image in the cell if it's smaller
                    offset_x = (cell_width - current_img.width) // 2
                    offset_y = (cell_height - current_img.height) // 2
                    
                    filmstrip.paste(current_img, (x + offset_x, y + offset_y), current_img)
                    logger.debug(f"Placed {img_path.name} at position ({row}, {col})")
                    
            except Exception as e:
                logger.error(f"Failed to add {img_path.name} to filmstrip: {str(e)}")
                continue
        
        # Construct filename: [name]_[FrameSize]_[TotalFrames]_[GridWidth]x[GridHeight].[ext]
        extension = save_format.lower()
        filename = f"{name}_{cell_width}x{cell_height}_{num_images}_{cols}x{rows}.{extension}"
        output_path = output_dir / filename

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if save_format.upper() == 'WEBP':
             filmstrip.save(output_path, 'WEBP', quality=quality)
        else:
             filmstrip.save(output_path, save_format.upper())
        
        logger.info(f"Filmstrip saved to {output_path}")
        logger.info(f"Final dimensions: {filmstrip_width}x{filmstrip_height}px")
        
        return output_path
    
    def create_filmstrip_from_dir(self, input_dir: Union[str, Path],
                                  output_path: Union[str, Path],
                                  grid_size: Optional[int] = None,
                                  quality: int = 90,
                                  pattern: str = '*.*',
                                  autocrop: bool = False,
                                  save_format: str = 'WEBP') -> Path:
        """
        Create filmstrip from all images in a directory.
        
        Args:
            input_dir: Directory containing images
            output_path: Path for output filmstrip
            grid_size: Override automatic grid size (optional)
            quality: WebP quality setting
            pattern: Glob pattern for finding images (default: *.*)
            autocrop: If True, crop images to their visible content
            save_format: Output format ('WEBP' or 'PNG')
            
        Returns:
            Path to created filmstrip
        """
        input_dir = Path(input_dir)
        
        if not input_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {input_dir}")
        
        # Find all image files
        image_files = sorted(input_dir.glob(pattern), 
                           key=lambda p: self.natural_sort_key(p.name))
        
        # Filter for common image formats
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}
        image_files = [f for f in image_files 
                      if f.suffix.lower() in valid_extensions]
        
        if not image_files:
            raise ValueError(f"No image files found in {input_dir}")
        
        logger.info(f"Found {len(image_files)} images in {input_dir}")
        
        return self.create_filmstrip(image_files, output_path, name=input_dir.name, 
                                   grid_size=grid_size, quality=quality, 
                                   autocrop=autocrop, save_format=save_format)
