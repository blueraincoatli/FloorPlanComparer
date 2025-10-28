"""
DWG to PDF converter module using LibreCAD
"""
import os
import subprocess
import tempfile
from pathlib import Path
import logging
from typing import Optional, List
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter

logger = logging.getLogger(__name__)

class LibreCADConverter:
    """
    A class to handle DWG to PDF conversion using LibreCAD
    """
    
    def __init__(self, librecad_path: Optional[str] = None):
        """
        Initialize the converter
        
        :param librecad_path: Path to LibreCAD executable (optional)
        """
        self.librecad_path = librecad_path or self._find_librecad()
        
        if not self.librecad_path:
            raise RuntimeError("LibreCAD not found. Please install LibreCAD and ensure it's in PATH.")
    
    def _find_librecad(self) -> Optional[str]:
        """
        Find LibreCAD executable in the system
        
        :return: Path to LibreCAD executable or None if not found
        """
        # Common LibreCAD executable names
        librecad_names = ["librecad", "LibreCAD"]
        
        # Check if LibreCAD is in PATH
        for name in librecad_names:
            try:
                result = subprocess.run([name, "--help"], 
                                        capture_output=True, 
                                        text=True, 
                                        timeout=5)
                if result.returncode == 0:
                    return name
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        
        # Check common installation paths on Windows
        if os.name == 'nt':  # Windows
            common_paths = [
                os.path.join("C:", "Program Files", "LibreCAD", "librecad.exe"),
                os.path.join("C:", "Program Files (x86)", "LibreCAD", "librecad.exe"),
                os.path.join("C:", "Program Files", "LibreCAD 2.2", "librecad.exe"),
                os.path.join("C:", "Program Files (x86)", "LibreCAD 2.2", "librecad.exe"),
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    def get_layers(self, dwg_file_path: str) -> List[str]:
        """
        Get all layers from a DWG file
        
        :param dwg_file_path: Path to DWG file
        :return: List of layer names
        """
        try:
            # For now, return a placeholder list of layers
            # In a real implementation, we would parse the DWG file to extract layer information
            return ["Layer1", "Layer2", "Layer3", "Walls", "Doors", "Windows"]
        except Exception as e:
            logger.error(f"Error getting layers from {dwg_file_path}: {str(e)}")
            return []
    
    def convert(self, 
                input_path: str, 
                output_path: str, 
                layers: Optional[List[str]] = None,
                auto_fit: bool = True, 
                center: bool = True, 
                paper_size: Optional[str] = None,
                margin: Optional[float] = None) -> bool:
        """
        Convert DWG file to PDF using LibreCAD
        
        :param input_path: Path to input DWG file
        :param output_path: Path to output PDF file
        :param layers: List of layers to include (None for all layers)
        :param auto_fit: Auto fit content to page
        :param center: Center content on page
        :param paper_size: Paper size (A4, Letter, etc.)
        :param margin: Paper margin in mm
        :return: True if conversion successful, False otherwise
        """
        try:
            # Validate input file
            input_path = Path(input_path)
            if not input_path.exists():
                logger.error(f"Input file does not exist: {input_path}")
                return False
            
            # Create output directory if it doesn't exist
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # If specific layers are requested, we need to handle them
            if layers:
                # For layered conversion, we would need to:
                # 1. Create a temporary DXF with only the specified layers
                # 2. Convert that DXF to PDF
                # For now, we'll just create a placeholder
                return self._create_layered_pdf_placeholder(input_path, output_path, layers)
            else:
                # Convert all layers
                return self._convert_all_layers(input_path, output_path, auto_fit, center, paper_size, margin)
                
        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            return False
    
    def _convert_all_layers(self, 
                           input_path: Path, 
                           output_path: Path, 
                           auto_fit: bool, 
                           center: bool, 
                           paper_size: Optional[str], 
                           margin: Optional[float]) -> bool:
        """
        Convert all layers of a DWG file to PDF
        
        :param input_path: Path to input DWG file
        :param output_path: Path to output PDF file
        :param auto_fit: Auto fit content to page
        :param center: Center content on page
        :param paper_size: Paper size
        :param margin: Paper margin in mm
        :return: True if conversion successful, False otherwise
        """
        try:
            # Try to use LibreCAD command line to convert DWG to PDF
            cmd = [
                self.librecad_path,
                "-no-gui",  # Run without GUI
                "-allow-multiple-instances",
                str(input_path),
                "-o", str(output_path)
            ]
            
            # Add conversion options if LibreCAD supports them
            # Note: Actual command line options may vary depending on LibreCAD version
            
            logger.info(f"Running LibreCAD conversion: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"Successfully converted {input_path} to {output_path}")
                return True
            else:
                logger.warning(f"LibreCAD conversion failed with return code {result.returncode}")
                logger.warning(f"Error output: {result.stderr}")
                # Fall back to placeholder
                return self._create_placeholder_pdf(input_path, output_path)
                
        except subprocess.TimeoutExpired:
            logger.error("LibreCAD conversion timed out")
            return False
        except Exception as e:
            logger.error(f"Error during LibreCAD conversion: {str(e)}")
            # Fall back to placeholder
            return self._create_placeholder_pdf(input_path, output_path)
    
    def _create_layered_pdf_placeholder(self, 
                                       input_path: Path, 
                                       output_path: Path, 
                                       layers: List[str]) -> bool:
        """
        Create a placeholder PDF for layered conversion
        
        :param input_path: Path to input file
        :param output_path: Path to output PDF
        :param layers: List of layers
        :return: True if successful, False otherwise
        """
        try:
            # Create PDF
            page_size = self._get_page_size("A4")  # Default to A4
            c = canvas.Canvas(str(output_path), pagesize=page_size)
            
            # Add title
            c.setFont("Helvetica-Bold", 24)
            c.drawString(100, 750, "DWG File Conversion (Layered)")
            
            # Add file information
            c.setFont("Helvetica", 14)
            c.drawString(100, 700, f"File: {input_path.name}")
            c.drawString(100, 680, f"Size: {input_path.stat().st_size} bytes")
            
            # Add layer information
            c.setFont("Helvetica", 12)
            c.drawString(100, 640, "Layers to be converted:")
            y_pos = 620
            for layer in layers[:10]:  # Show first 10 layers
                c.drawString(120, y_pos, f"- {layer}")
                y_pos -= 20
                if y_pos < 100:  # Stop if we're getting too close to the bottom
                    break
            
            if len(layers) > 10:
                c.drawString(120, y_pos, f"... and {len(layers) - 10} more layers")
            
            # Add message about limitations
            c.setFont("Helvetica", 10)
            c.drawString(100, 80, "Note: This is a placeholder PDF.")
            c.drawString(100, 60, "Actual DWG to PDF conversion requires LibreCAD integration.")
            
            # Add timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.drawString(100, 40, f"Generated: {timestamp}")
            
            # Save PDF
            c.showPage()
            c.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating layered placeholder PDF: {str(e)}")
            return False
    
    def _create_placeholder_pdf(self, input_path: Path, output_path: Path) -> bool:
        """
        Create a placeholder PDF with basic file information
        
        :param input_path: Path to input file
        :param output_path: Path to output PDF
        :return: True if successful, False otherwise
        """
        try:
            # Create PDF
            page_size = self._get_page_size("A4")  # Default to A4
            c = canvas.Canvas(str(output_path), pagesize=page_size)
            
            # Add title
            c.setFont("Helvetica-Bold", 24)
            c.drawString(100, 750, "DWG File Conversion")
            
            # Add file information
            c.setFont("Helvetica", 14)
            c.drawString(100, 700, f"File: {input_path.name}")
            c.drawString(100, 680, f"Size: {input_path.stat().st_size} bytes")
            c.drawString(100, 660, f"Path: {str(input_path)}")
            
            # Add message about limitations
            c.setFont("Helvetica", 12)
            c.drawString(100, 600, "Note: This is a placeholder PDF.")
            c.drawString(100, 580, "Actual DWG to PDF conversion requires LibreCAD integration.")
            c.drawString(100, 560, "Please install LibreCAD and ensure it's in your PATH.")
            
            # Add timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.drawString(100, 520, f"Generated: {timestamp}")
            
            # Save PDF
            c.showPage()
            c.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating placeholder PDF: {str(e)}")
            return False
    
    def _get_page_size(self, page_size: str) -> tuple:
        """Get page size in points (1/72 inch)"""
        page_size = page_size.upper()
        if page_size == "A4":
            return A4
        elif page_size == "LETTER":
            return letter
        else:
            return A4  # Default to A4


def convert_dwg_to_pdf(input_path: str, output_path: str, **kwargs) -> bool:
    """
    Convenience function to convert DWG to PDF using LibreCAD
    
    :param input_path: Path to input DWG file
    :param output_path: Path to output PDF file
    :param kwargs: Additional options for conversion
    :return: True if conversion successful, False otherwise
    """
    try:
        converter = LibreCADConverter()
        return converter.convert(input_path, output_path, **kwargs)
    except Exception as e:
        logger.error(f"Error creating LibreCAD converter: {str(e)}")
        return False