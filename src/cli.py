"""Command-Line Interface Module

This module provides the CLI for the PNG to WebP filmstrip converter.
"""

import click
import logging
from pathlib import Path
from tqdm import tqdm
from src.converter import PNGConverter
from src.filmstrip import FilmstripGenerator


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


@click.group()
def cli():
    """PNG to WebP Filmstrip Converter
    
    Convert PNG images to WebP format and arrange them into optimized n×n grid filmstrips.
    """
    pass


@cli.command()
@click.option('-i', '--input', 'input_dir', required=True, type=click.Path(exists=True),
              help='Input directory containing PNG files')
@click.option('-o', '--output', 'output_dir', type=click.Path(),
              help='Output directory for WebP files (default: same as input)')
@click.option('-q', '--quality', default=90, type=click.IntRange(0, 100),
              help='WebP quality (0-100, default: 90)')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
def convert(input_dir, output_dir, quality, verbose):
    """Convert PNG files to WebP format (without creating filmstrip)."""
    setup_logging(verbose)
    
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path
    
    click.echo(f"Converting PNG files from: {input_path}")
    click.echo(f"Output directory: {output_path}")
    click.echo(f"Quality: {quality}")
    
    converter = PNGConverter(quality=quality)
    png_files = converter.get_png_files(input_path)
    
    if not png_files:
        click.echo("❌ No PNG files found in input directory", err=True)
        return
    
    click.echo(f"Found {len(png_files)} PNG files")
    
    # Convert with progress bar
    converted = []
    with tqdm(total=len(png_files), desc="Converting", unit="file") as pbar:
        for png_file in png_files:
            try:
                output_file = output_path / png_file.with_suffix('.webp').name
                converter.convert_single(png_file, output_file)
                converted.append(output_file)
                pbar.update(1)
            except Exception as e:
                click.echo(f"❌ Failed to convert {png_file.name}: {str(e)}", err=True)
                pbar.update(1)
    
    click.echo(f"✅ Successfully converted {len(converted)} of {len(png_files)} files")


@cli.command()
@click.option('-i', '--input', 'input_dir', required=True, type=click.Path(exists=True),
              help='Input directory containing images')
@click.option('-o', '--output', 'output_dir', required=True, type=click.Path(),
              help='Output directory for filmstrip')
@click.option('-q', '--quality', default=90, type=click.IntRange(0, 100),
              help='WebP quality (0-100, default: 90)')
@click.option('-g', '--grid-size', type=int,
              help='Override automatic grid size calculation (n for n×n grid)')
@click.option('--convert-png', is_flag=True,
              help='Convert PNG files to WebP first before creating filmstrip')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
def filmstrip(input_dir, output_dir, quality, grid_size, convert_png, verbose):
    """Create an n×n grid filmstrip from images."""
    setup_logging(verbose)
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    click.echo(f"Creating filmstrip from: {input_path}")
    click.echo(f"Output directory: {output_path}")
    click.echo(f"Quality: {quality}")
    
    # Convert PNG to WebP first if requested
    if convert_png:
        click.echo("\n📸 Converting PNG files to WebP first...")
        converter = PNGConverter(quality=quality)
        png_files = converter.get_png_files(input_path)
        
        if png_files:
            with tqdm(total=len(png_files), desc="Converting", unit="file") as pbar:
                for png_file in png_files:
                    try:
                        converter.convert_single(png_file)
                        pbar.update(1)
                    except Exception as e:
                        click.echo(f"Warning: Failed to convert {png_file.name}", err=True)
                        pbar.update(1)
    
    # Create filmstrip
    click.echo("\n🎬 Creating filmstrip...")
    generator = FilmstripGenerator()
    
    try:
        result = generator.create_filmstrip_from_dir(
            input_path,
            output_path,
            grid_size=grid_size,
            quality=quality
        )
        
        # Get file size
        file_size = result.stat().st_size / 1024  # KB
        
        click.echo(f"\n✅ Filmstrip created successfully!")
        click.echo(f"📁 Output: {result}")
        click.echo(f"📊 File size: {file_size:.2f} KB")
        
    except Exception as e:
        click.echo(f"❌ Failed to create filmstrip: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.option('-i', '--input', 'input_dir', required=True, type=click.Path(exists=True),
              help='Input directory containing PNG files')
@click.option('-o', '--output', 'output_dir', required=True, type=click.Path(),
              help='Output directory for filmstrip')
@click.option('-q', '--quality', default=90, type=click.IntRange(0, 100),
              help='WebP quality (0-100, default: 90)')
@click.option('-g', '--grid-size', type=int,
              help='Override automatic grid size calculation')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
def process(input_dir, output_dir, quality, grid_size, verbose):
    """Complete workflow: Convert PNGs to WebP and create filmstrip.
    
    This is the recommended command that combines conversion and filmstrip creation.
    """
    setup_logging(verbose)
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    click.echo("=" * 60)
    click.echo("PNG to WebP Filmstrip Converter")
    click.echo("=" * 60)
    click.echo(f"Input directory: {input_path}")
    click.echo(f"Output directory: {output_path}")
    click.echo(f"Quality: {quality}")
    if grid_size:
        click.echo(f"Grid size: {grid_size}×{grid_size}")
    click.echo("=" * 60)
    
    # Step 1: Convert PNG to WebP
    click.echo("\n📸 Step 1: Converting PNG files to WebP...")
    converter = PNGConverter(quality=quality)
    png_files = converter.get_png_files(input_path)
    
    if not png_files:
        click.echo("❌ No PNG files found in input directory", err=True)
        return
    
    click.echo(f"Found {len(png_files)} PNG files")
    
    converted = []
    with tqdm(total=len(png_files), desc="Converting", unit="file") as pbar:
        for png_file in png_files:
            try:
                converter.convert_single(png_file)
                converted.append(png_file.with_suffix('.webp'))
                pbar.update(1)
            except Exception as e:
                click.echo(f"Warning: Failed to convert {png_file.name}", err=True)
                pbar.update(1)
    
    click.echo(f"✅ Converted {len(converted)} files")
    
    # Step 2: Create filmstrip
    click.echo("\n🎬 Step 2: Creating filmstrip from WebP images...")
    generator = FilmstripGenerator()
    
    try:
        # Use converted WebP files
        webp_files = list(input_path.glob('*.webp'))
        
        if not webp_files:
            click.echo("❌ No WebP files found for filmstrip creation", err=True)
            return
        
        result = generator.create_filmstrip(
            webp_files,
            output_path,
            name=input_path.name,
            grid_size=grid_size,
            quality=quality
        )
        
        # Calculate statistics
        file_size = result.stat().st_size / 1024  # KB
        total_original = sum(f.stat().st_size for f in png_files) / 1024
        savings = ((total_original - file_size) / total_original * 100) if total_original > 0 else 0
        
        click.echo(f"\n✅ Filmstrip created successfully!")
        click.echo(f"📁 Output: {result}")
        click.echo(f"📊 File size: {file_size:.2f} KB")
        click.echo(f"💾 Original PNGs: {total_original:.2f} KB")
        click.echo(f"🎯 Space savings: {savings:.1f}%")
        
    except Exception as e:
        click.echo(f"❌ Failed to create filmstrip: {str(e)}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
