"""
DWG to PDF converter module using AutoCAD
"""
import os
import tempfile
from pathlib import Path
import logging
from typing import Optional, Tuple
import subprocess
import time
import win32com.client
import pythoncom

logger = logging.getLogger(__name__)

class DWGToPDFConverter:
    """
    A class to handle DWG to PDF conversion using AutoCAD
    """
    
    def __init__(self, autocad_path: Optional[str] = None):
        """
        Initialize the converter
        
        :param autocad_path: Path to AutoCAD executable (optional)
        """
        self.autocad_path = autocad_path
    
    def convert(self, 
                input_path: str, 
                output_path: str, 
                auto_fit: bool = True, 
                center: bool = True, 
                paper_size: Optional[str] = None,
                margin: Optional[float] = None,
                grayscale: bool = False,
                monochrome: bool = False) -> bool:
        """
        Convert DWG file to PDF using AutoCAD
        
        :param input_path: Path to input DWG file
        :param output_path: Path to output PDF file
        :param auto_fit: Auto fit content to page
        :param center: Center content on page
        :param paper_size: Paper size for output
        :param margin: Paper margin in mm
        :param grayscale: Convert to grayscale
        :param monochrome: Convert to monochrome (black/white)
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
            
            # Use AutoCAD to convert DWG to PDF
            success = self._convert_with_autocad(input_path, output_path)
            
            if success:
                logger.info(f"Successfully converted {input_path} to {output_path}")
            else:
                logger.error(f"Failed to convert {input_path} to PDF")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            return False
    
    def _convert_with_autocad(self, input_path: Path, output_path: Path) -> bool:
        """
        Convert DWG to PDF using AutoCAD COM interface
        
        :param input_path: Path to input DWG file
        :param output_path: Path to output PDF file
        :return: True if successful, False otherwise
        """
        try:
            # Initialize COM
            pythoncom.CoInitialize()
            
            # Connect to AutoCAD
            acad = win32com.client.Dispatch("AutoCAD.Application")
            acad.Visible = False  # Run in background
            
            # Open the DWG file
            doc = acad.Documents.Open(str(input_path))
            
            # Wait for document to load
            time.sleep(1)
            
            # Set the active layout to Model
            layout = None
            for layout_obj in doc.Layouts:
                if layout_obj.Name == "Model":
                    layout = layout_obj
                    break
            
            if layout is None:
                # If Model layout not found, use the first layout
                layout = doc.Layouts.Item(0)
            
            # Set the layout as current
            doc.ActiveLayout = layout
            
            # Export to PDF
            doc.Export(str(output_path), "PDF", "")
            
            # Close the document without saving
            doc.Close(SaveChanges=False)
            
            # Clean up
            del doc
            del acad
            
            # Uninitialize COM
            pythoncom.CoUninitialize()
            
            return True
            
        except Exception as e:
            logger.error(f"Error converting with AutoCAD: {str(e)}")
            try:
                pythoncom.CoUninitialize()
            except:
                pass
            return False


def convert_dwg_to_pdf(input_path: str, output_path: str, **kwargs) -> bool:
    """
    Convenience function to convert DWG to PDF
    
    :param input_path: Path to input DWG file
    :param output_path: Path to output PDF file
    :param kwargs: Additional options for conversion
    :return: True if conversion successful, False otherwise
    """
    converter = DWGToPDFConverter()
    return converter.convert(input_path, output_path, **kwargs)