"""
PDF comparison service for detecting differences between floor plans
"""
import cv2
import numpy as np
from pdf2image import convert_from_path
from skimage.metrics import structural_similarity as ssim
from pathlib import Path
import logging
from typing import Tuple, List, Optional
import json

logger = logging.getLogger(__name__)

class PDFComparator:
    """
    A class to compare PDF files and detect differences
    """
    
    def __init__(self, dpi: int = 300):
        """
        Initialize the comparator
        
        :param dpi: Resolution for PDF to image conversion
        """
        self.dpi = dpi
    
    def compare_pdfs(self, 
                     pdf1_path: str, 
                     pdf2_path: str, 
                     output_image_path: Optional[str] = None,
                     output_json_path: Optional[str] = None) -> dict:
        """
        Compare two PDF files and generate difference report
        
        :param pdf1_path: Path to first PDF file (original)
        :param pdf2_path: Path to second PDF file (modified)
        :param output_image_path: Path to save difference image (optional)
        :param output_json_path: Path to save JSON report (optional)
        :return: Dictionary with comparison results
        """
        try:
            # Validate input files
            pdf1_path = Path(pdf1_path)
            pdf2_path = Path(pdf2_path)
            
            if not pdf1_path.exists():
                raise FileNotFoundError(f"Original PDF not found: {pdf1_path}")
            
            if not pdf2_path.exists():
                raise FileNotFoundError(f"Modified PDF not found: {pdf2_path}")
            
            # Convert PDFs to images
            logger.info("Converting PDFs to images...")
            img1 = self._pdf_to_image(pdf1_path)
            img2 = self._pdf_to_image(pdf2_path)
            
            if img1 is None or img2 is None:
                raise ValueError("Failed to convert PDFs to images")
            
            # Detect changes
            logger.info("Detecting changes...")
            diff_image, contours, stats = self._detect_changes(img1, img2)
            
            # Prepare results
            result = {
                "original_pdf": str(pdf1_path),
                "modified_pdf": str(pdf2_path),
                "change_count": len(contours),
                "total_area": stats["total_area"],
                "change_percentage": stats["change_percentage"],
                "contours": [
                    {
                        "area": cv2.contourArea(contour),
                        "bbox": cv2.boundingRect(contour)
                    }
                    for contour in contours
                ]
            }
            
            # Save difference image if requested
            if output_image_path:
                output_image_path = Path(output_image_path)
                output_image_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(output_image_path), diff_image)
                result["difference_image"] = str(output_image_path)
                logger.info(f"Difference image saved to {output_image_path}")
            
            # Save JSON report if requested
            if output_json_path:
                output_json_path = Path(output_json_path)
                output_json_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_json_path, 'w') as f:
                    json.dump(result, f, indent=2)
                result["json_report"] = str(output_json_path)
                logger.info(f"JSON report saved to {output_json_path}")
            
            logger.info(f"Comparison completed: {len(contours)} changes detected")
            return result
            
        except Exception as e:
            logger.error(f"Error during PDF comparison: {str(e)}")
            raise
    
    def _pdf_to_image(self, pdf_path: Path) -> Optional[np.ndarray]:
        """
        Convert PDF to image
        
        :param pdf_path: Path to PDF file
        :return: Image as numpy array or None if failed
        """
        try:
            images = convert_from_path(str(pdf_path), dpi=self.dpi, first_page=1, last_page=1)
            if images:
                # Convert PIL image to OpenCV format
                img = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
                return img
            return None
        except Exception as e:
            logger.error(f"Error converting PDF to image: {str(e)}")
            return None
    
    def _detect_changes(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[np.ndarray, List, dict]:
        """
        Detect changes between two images
        
        :param img1: First image (original)
        :param img2: Second image (modified)
        :return: Tuple of (difference image, contours, statistics)
        """
        # Convert to grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Calculate difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Apply threshold
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to clean up
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter small contours
        min_area = 100
        contours = [c for c in contours if cv2.contourArea(c) > min_area]
        
        # Create difference image with color coding
        result = img2.copy()
        
        # Color code differences
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Sample region values to determine change type
                region1 = gray1[y:y+h, x:x+w]
                region2 = gray2[y:y+h, x:x+w]
                
                mean1 = np.mean(region1) if region1.size > 0 else 0
                mean2 = np.mean(region2) if region2.size > 0 else 0
                
                # Color code based on change type
                if mean2 > mean1:  # Brighter (addition)
                    color = (0, 255, 0)  # Green
                elif mean2 < mean1:  # Darker (deletion)
                    color = (0, 0, 255)  # Red
                else:  # Same brightness (modification)
                    color = (255, 255, 0)  # Yellow
                
                # Draw rectangle
                cv2.rectangle(result, (x, y), (x+w, y+h), color, 2)
        
        # Calculate statistics
        total_area = sum(cv2.contourArea(c) for c in contours)
        image_area = img1.shape[0] * img1.shape[1]
        change_percentage = (total_area / image_area) * 100 if image_area > 0 else 0
        
        stats = {
            "total_area": total_area,
            "change_percentage": change_percentage
        }
        
        return result, contours, stats


def compare_floor_plans(original_pdf: str, modified_pdf: str, **kwargs) -> dict:
    """
    Convenience function to compare floor plan PDFs
    
    :param original_pdf: Path to original PDF
    :param modified_pdf: Path to modified PDF
    :param kwargs: Additional options
    :return: Comparison results
    """
    comparator = PDFComparator()
    return comparator.compare_pdfs(original_pdf, modified_pdf, **kwargs)