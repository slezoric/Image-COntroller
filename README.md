# PNG to WebP Filmstrip Converter

A Python-based tool to convert PNG images to WebP format and arrange them into optimized n×n grid filmstrips, maximizing WebP's resolution capabilities.

## Features

- 🔄 **PNG to WebP Conversion**: Convert PNG images to WebP format with configurable quality settings
- 🎬 **Grid Filmstrip Generation**: Automatically arrange images into optimal n×n grids
- 📊 **Smart Grid Calculation**: Automatic calculation of grid size (e.g., 9 images → 3×3, 10 images → 4×4)
- 🎨 **Transparency Support**: Preserves alpha channels and transparency
- 📈 **Progress Tracking**: Visual progress bars for batch operations
- 💾 **Space Savings**: Significant file size reduction compared to PNG

## Installation

### Prerequisites

- Python 3.7 or higher
- pip

### Setup

1. Clone or download this repository
2. Navigate to the project directory
3. Run the setup script to create a virtual environment and install dependencies:

```bash
./setup.sh
```

4. Activate the virtual environment:

```bash
source venv/bin/activate
```

Alternatively, you can set it up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

The tool provides three main commands:

### 1. Complete Workflow (Recommended)

Convert PNGs to WebP and create filmstrip in one step:

```bash
python main.py process -i /path/to/input -o output/filmstrip.webp
```

**Options:**
- `-i, --input`: Input directory containing PNG files (required)
- `-o, --output`: Output WebP filmstrip file path (required)
- `-q, --quality`: WebP quality 0-100 (default: 90)
- `-g, --grid-size`: Override automatic grid size (e.g., `-g 4` for 4×4)
- `-v, --verbose`: Enable verbose logging

**Example:**
```bash
python main.py process -i ./images -o ./output/filmstrip.webp -q 85
```

### 2. Convert Only

Convert PNG files to WebP without creating filmstrip:

```bash
python main.py convert -i /path/to/input -o /path/to/output
```

**Options:**
- `-i, --input`: Input directory containing PNG files (required)
- `-o, --output`: Output directory (default: same as input)
- `-q, --quality`: WebP quality 0-100 (default: 90)
- `-v, --verbose`: Enable verbose logging

**Example:**
```bash
python main.py convert -i ./images -q 90
```

### 3. Filmstrip Only

Create filmstrip from existing images:

```bash
python main.py filmstrip -i /path/to/images -o filmstrip.webp
```

**Options:**
- `-i, --input`: Input directory containing images (required)
- `-o, --output`: Output filmstrip file path (required)
- `-q, --quality`: WebP quality 0-100 (default: 90)
- `-g, --grid-size`: Override automatic grid size
- `--convert-png`: Convert PNG files to WebP first
- `-v, --verbose`: Enable verbose logging

**Example:**
```bash
python main.py filmstrip -i ./webp_images -o output.webp -g 5
```

## How It Works

### Grid Size Calculation

The tool automatically calculates the optimal n×n grid size:

- **Perfect squares**: 9 images → 3×3 grid, 16 images → 4×4 grid
- **Non-perfect squares**: Rounds up to next square (10 images → 4×4 grid with 6 empty cells)
- **Manual override**: Use `-g` option to specify custom grid size

### Image Arrangement

Images are arranged in the grid:
- **Order**: Left to right, top to bottom
- **Centering**: Smaller images are centered within their cells
- **Cell size**: Based on the largest image dimensions
- **Empty cells**: Filled with transparent background

### WebP Quality

Quality settings affect file size and visual quality:
- **90 (default)**: Excellent quality, good compression
- **75-85**: Good quality, better compression
- **50-70**: Acceptable quality, high compression
- **100**: Lossless (large file size)

## Examples

### Basic Usage

Convert 9 PNG files and create a 3×3 filmstrip:

```bash
# Create sample PNGs (optional)
python -c "from PIL import Image; [Image.new('RGB', (100, 100), color=(255*i//9, 100, 200)).save(f'image_{i}.png') for i in range(9)]"

# Process them
python main.py process -i . -o filmstrip.webp
```

### Custom Quality

High compression for web use:

```bash
python main.py process -i ./images -o web_filmstrip.webp -q 75
```

### Override Grid Size

Force a 5×5 grid even with fewer images:

```bash
python main.py process -i ./images -o filmstrip.webp -g 5
```

### Verbose Output

See detailed logging:

```bash
python main.py process -i ./images -o filmstrip.webp -v
```

## Project Structure

```
png-to-webp-filmstrip/
├── src/
│   ├── __init__.py
│   ├── converter.py      # PNG to WebP conversion logic
│   ├── filmstrip.py      # Grid layout generator
│   └── cli.py            # Command-line interface
├── tests/
│   ├── __init__.py
│   └── test_sample_images/
├── requirements.txt       # Python dependencies
├── main.py               # Entry point
└── README.md             # This file
```

## Requirements

- **Pillow**: Image processing library with PNG/WebP support
- **click**: Command-line interface framework
- **tqdm**: Progress bar library

## Technical Details

### Supported Image Formats

- **Input**: PNG (primary), JPG, JPEG, BMP, GIF, WebP
- **Output**: WebP (filmstrip), WebP (converted images)

### Transparency Handling

- RGBA images preserve alpha channels
- LA (grayscale + alpha) images supported
- RGB images converted as-is
- Transparent background for empty grid cells

### Performance

- Batch processing with error recovery
- Memory-efficient image handling
- Progress bars for long operations

## Troubleshooting

### "No PNG files found"

Ensure your input directory contains `.png` files (case-sensitive on some systems).

### "Grid size too small"

If you override grid size, ensure n×n ≥ number of images. Use automatic calculation or increase grid size.

### "Failed to convert"

Check that input files are valid PNG images. Corrupted files are skipped with warnings.

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.
