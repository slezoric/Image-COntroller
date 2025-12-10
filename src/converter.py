"""PNG to WebP Converter Module

This module handles the conversion of PNG images to WebP format with
configurable quality settings and batch processing support.
"""

import os
from pathlib import Path
from typing import List, Union, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class PNGConverter:
    """Handles conversion of PNG images to WebP format."""
    
    def __init__(self, quality: int = 90):
        """
        Initialize the PNG converter.
        
        Args:
            quality: WebP quality setting (0-100), default is 90
        """
        if not 0 <= quality <= 100:
            raise ValueError("Quality must be between 0 and 100")
        self.quality = quality
    
    def convert_single(self, input_path: Union[str, Path], 
                      output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Convert a single PNG image to WebP format.
        
        Args:
            input_path: Path to input PNG file
            output_path: Path for output WebP file (optional, auto-generated if None)
            
        Returns:
            Path to the created WebP file
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If input file is not a PNG
            IOError: If conversion fails
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if input_path.suffix.lower() != '.png':
            raise ValueError(f"Input file must be PNG: {input_path}")
        
        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.with_suffix('.webp')
        else:
            output_path = Path(output_path)
        
        try:
            # Open and convert the image
            with Image.open(input_path) as img:
                # Preserve transparency if present
                if img.mode in ('RGBA', 'LA'):
                    img.save(output_path, 'WEBP', quality=self.quality, 
                            lossless=False)
                else:
                    # Convert to RGB if not already
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(output_path, 'WEBP', quality=self.quality)
            
            logger.info(f"Converted {input_path.name} -> {output_path.name}")
            return output_path
            
        except Exception as e:
            raise IOError(f"Failed to convert {input_path}: {str(e)}")
    
    def convert_batch(self, input_dir: Union[str, Path], 
                     output_dir: Optional[Union[str, Path]] = None) -> List[Path]:
        """
        Convert all PNG files in a directory to WebP format.
        
        Args:
            input_dir: Directory containing PNG files
            output_dir: Directory for output WebP files (optional, uses input_dir if None)
            
        Returns:
            List of paths to created WebP files
            
        Raises:
            NotADirectoryError: If input_dir is not a directory
        """
        input_dir = Path(input_dir)
        
        if not input_dir.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {input_dir}")
        
        # Use input directory if output not specified
        if output_dir is None:
            output_dir = input_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all PNG files
        png_files = sorted(input_dir.glob('*.png'))
        
        if not png_files:
            logger.warning(f"No PNG files found in {input_dir}")
            return []
        
        # Convert each file
        converted_files = []
        for png_file in png_files:
            output_path = output_dir / png_file.with_suffix('.webp').name
            try:
                self.convert_single(png_file, output_path)
                converted_files.append(output_path)
            except Exception as e:
                logger.error(f"Failed to convert {png_file.name}: {str(e)}")
                continue
        
        logger.info(f"Converted {len(converted_files)} of {len(png_files)} files")
        return converted_files
    
    def get_png_files(self, directory: Union[str, Path]) -> List[Path]:
        """
        Get all PNG files from a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of PNG file paths
        """
        directory = Path(directory)
        return sorted(directory.glob('*.png'))
