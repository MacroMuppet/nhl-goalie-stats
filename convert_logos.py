#!/usr/bin/env python3
import os
import cairosvg
from PIL import Image
import io

# Create a list of NHL team shortcodes
TEAM_CODES = [
    'ANA', 'BOS', 'BUF', 'CAR', 'CBJ', 'CGY', 'CHI', 'COL',
    'DAL', 'DET', 'EDM', 'FLA', 'LAK', 'MIN', 'MTL', 'NJD',
    'NSH', 'NYI', 'NYR', 'OTT', 'PHI', 'PIT', 'SEA', 'SJS',
    'STL', 'TBL', 'TOR', 'VAN', 'VGK', 'WPG', 'WSH', 'ARI'
]

def convert_svg_to_jpg(svg_path, jpg_path, size=(200, 200)):
    try:
        # Convert SVG to PNG in memory with white background
        png_data = cairosvg.svg2png(
            url=svg_path,
            output_width=size[0],
            output_height=size[1],
            background_color='white'
        )
        
        # Open PNG data with PIL
        img = Image.open(io.BytesIO(png_data))
        
        # Convert to RGB mode (required for JPEG)
        img = img.convert('RGB')
        
        # Save as JPEG
        img.save(jpg_path, 'JPEG', quality=95)
        print(f"Successfully converted {os.path.basename(svg_path)} to JPG")
        
    except Exception as e:
        print(f"Error converting {os.path.basename(svg_path)}: {str(e)}")

def main():
    # Create Logos_JPG directory if it doesn't exist
    jpg_dir = "Logos_JPG"
    os.makedirs(jpg_dir, exist_ok=True)
    
    print(f"Created directory: {jpg_dir}")
    print("Starting SVG to JPG conversion...")
    
    # Convert each team logo
    for team_code in TEAM_CODES:
        svg_path = f"Logos/{team_code}_light.svg"
        jpg_path = f"{jpg_dir}/{team_code}_light.jpg"
        
        if os.path.exists(svg_path):
            convert_svg_to_jpg(svg_path, jpg_path)
        else:
            print(f"Warning: SVG file not found for {team_code}")
    
    print("\nConversion complete! Check the 'Logos_JPG' directory for the converted logos.")

if __name__ == "__main__":
    main() 