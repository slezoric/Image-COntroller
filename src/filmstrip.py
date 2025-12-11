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
                        padding: int = 0,
                        square: bool = False,
                        fixed_center: bool = False,
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
            if fixed_center:
                logger.info("Calculating optimal crop bounds (Center-Preserving)...")
                # 1. Calculate Global BBox first
                global_left = float('inf')
                global_top = float('inf')
                global_right = 0
                global_bottom = 0
                has_valid_content = False
                
                # We need image center for fixed-center logic
                # Assume all images are same size (they should be for animation frames)
                # But let's be safe and check per image or use first image dimensions
                # Actually, standard animation sprites are same canvas size.
                
                max_h_radius = 0
                max_v_radius = 0
                
                for img_path in valid_images:
                    try:
                        with Image.open(img_path) as img:
                            bbox = img.getbbox()
                            if bbox:
                                has_valid_content = True
                                cx = img.width / 2
                                cy = img.height / 2
                                
                                # Distances from center to bbox edges
                                # bbox is (left, top, right, bottom)
                                dist_l = abs(cx - bbox[0])
                                dist_r = abs(bbox[2] - cx)
                                dist_t = abs(cy - bbox[1])
                                dist_b = abs(bbox[3] - cy)
                                
                                max_h_radius = max(max_h_radius, dist_l, dist_r)
                                max_v_radius = max(max_v_radius, dist_t, dist_b)
                    except Exception as e:
                        logger.warning(f"Could not read {img_path}: {str(e)}")
                
                if has_valid_content:
                    # Calculate dimensions based on max radius
                    # ceil to ensure we cover it
                    cell_width = int(math.ceil(max_h_radius * 2))
                    cell_height = int(math.ceil(max_v_radius * 2))
                    
                    # Since we want to preserve center, we don't really construct a "crop box"
                    # in absolute coordinates for ALL images if they differ in size.
                    # But if they are same size, center is same.
                    # We will crop around center of each image dynamically.
                    # crop_box variable will be a tuple of (width, height) to indicate sizing strategy
                    crop_box = ("CENTER", cell_width, cell_height)
                    logger.info(f"Fixed Center Autocrop. Size: {cell_width}x{cell_height}")
                else:
                     logger.warning("Autocrop enabled but no content found.")
                     cell_width, cell_height = self.get_max_dimensions(valid_images)
                     crop_box = None

            else:
                # Classic Global BBox
                logger.info("Calculating optimal crop bounds (Global Bounding Box)...")
                global_left = float('inf')
                global_top = float('inf')
                global_right = 0
                global_bottom = 0
                has_valid_content = False
                
                for img_path in valid_images:
                    try:
                        with Image.open(img_path) as img:
                            bbox = img.getbbox()
                            if bbox:
                                has_valid_content = True
                                global_left = min(global_left, bbox[0])
                                global_top = min(global_top, bbox[1])
                                global_right = max(global_right, bbox[2])
                                global_bottom = max(global_bottom, bbox[3])
                    except Exception as e:
                        logger.warning(f"Could not read {img_path}: {str(e)}")
                
                if has_valid_content:
                    cell_width = int(global_right - global_left)
                    cell_height = int(global_bottom - global_top)
                    crop_box = (int(global_left), int(global_top), int(global_right), int(global_bottom))
                    logger.info(f"Global Autocrop. BBox: {crop_box}, Size: {cell_width}x{cell_height}")
                else:
                    logger.warning("Autocrop enabled but no content found.")
                    cell_width, cell_height = self.get_max_dimensions(valid_images)
                    crop_box = None
            
            # Apply padding if we have a crop
            if crop_box and padding > 0:
                cell_width += padding * 2
                cell_height += padding * 2
                logger.info(f"Applied padding {padding}px. New Size: {cell_width}x{cell_height}")
                
            # Apply Square constraint
            if crop_box and square:
                max_dim = max(cell_width, cell_height)
                cell_width = max_dim
                cell_height = max_dim
                logger.info(f"Squared output. Size: {cell_width}x{cell_height}")

        else:
            # Get maximum dimensions for uniform cell sizing (original size)
            cell_width, cell_height = self.get_max_dimensions(valid_images)
            crop_box = None
            

        
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
                        if isinstance(crop_box, tuple) and crop_box[0] == "CENTER":
                            # Fixed Center Logic: Crop around image center to target size (minus padding)
                            # cell_width includes padding. We want strictly the content size first? 
                            # No, we calculated cell_width based on radius. 
                            # If padding was added, cell_width is bigger.
                            # We need to paste the image centered in the cell.
                            # Actually, for "CENTER" mode, we just crop the original image with a box centered on its center
                            # with size = cell_width - 2*padding?
                            # Optimally: Just take original image and center it in the target cell.
                            # Because the cell size was calculated TO FIT the rotation.
                            # So we don't need to "crop" pixels out if the image is transparent.
                            # We just need to place it correctly.
                            
                            # BUT if we want to mimic "crop", we should ensure we don't draw outside?
                            # For RGBA, simpler is better:
                            # 1. Image is originally WxH.
                            # 2. Target cell is cell_width x cell_height.
                            # 3. We calculated cell dimensions to be large enough to contain the content relative to center.
                            # 4. We just center the *Original Image* (or its bbox?)
                            # Wait, "Center-Preserving Autocrop" means:
                            # The CENTER of the input image maps to the CENTER of the output cell.
                            # So:
                            dest_x = (cell_width - current_img.width) // 2
                            dest_y = (cell_height - current_img.height) // 2
                            
                            # If we just paste, we are good.
                            # Do we need to "crop"? Only if the image is LARGER than the cell?
                            # Our logic for cell size covers the content.
                            # But if the image has "junk" far away that we wanted to crop out?
                            # Classic autocrop removes junk. Fixed-Center autocrop assumes "junk" defines the radius?
                            # Using max_h_radius ensures all *content* fits.
                            # So pasting centered is correct.
                            pass
                        
                        elif crop_box:
                            # Classic Global BBox Logic
                            # crop_box is (left, top, right, bottom)
                            # We need to crop the image.
                            # current_img = img.crop(crop_box)
                            # This gives us the content. 
                            # Then we center it in the cell (which might be larger due to padding/square)
                            
                            cropped_img = img.crop(crop_box)
                            current_img = cropped_img
                    
                    # Center the image in the cell
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
                                  padding: int = 0,
                                  square: bool = False,
                                  fixed_center: bool = False,
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
        
        return self.create_filmstrip(image_paths=image_files, output_dir=output_path, 
                                   name=input_dir.name, 
                                   grid_size=grid_size, quality=quality, 
                                   autocrop=autocrop, padding=padding,
                                   square=square, fixed_center=fixed_center,
                                   save_format=save_format)
