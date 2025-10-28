"""
Test script for DWG to PDF converter
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from modules.dwg_to_pdf.converter import DWGToPDFConverter

def test_conversion():
    """Test the DWG to PDF conversion"""
    # Find sample DWG files in originFile directory
    origin_dir = Path(__file__).parent.parent.parent.parent.parent / "originFile"
    if not origin_dir.exists():
        print(f"Origin directory not found: {origin_dir}")
        return
    
    # Look for DWG files
    dwg_files = list(origin_dir.glob("*.dwg"))
    if not dwg_files:
        print("No DWG files found in originFile directory")
        return
    
    print(f"Found {len(dwg_files)} DWG files:")
    for dwg_file in dwg_files:
        print(f"  - {dwg_file.name}")
    
    # Create output directory
    output_dir = Path(__file__).parent.parent.parent.parent.parent / "temp" / "pdf_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert each DWG file
    converter = DWGToPDFConverter()
    
    for dwg_file in dwg_files[:2]:  # Limit to first 2 files for testing
        output_file = output_dir / f"{dwg_file.stem}_converted.pdf"
        print(f"\nConverting {dwg_file.name} to {output_file.name}...")
        
        success = converter.convert(
            input_path=str(dwg_file),
            output_path=str(output_file),
            auto_fit=True,
            center=True
        )
        
        if success:
            print(f"Successfully converted {dwg_file.name}")
            if output_file.exists():
                print(f"Output file size: {output_file.stat().st_size} bytes")
            else:
                print("Warning: Output file was not created")
        else:
            print(f"Failed to convert {dwg_file.name}")

if __name__ == "__main__":
    test_conversion()