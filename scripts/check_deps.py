# Check dependencies
try:
    import win32com.client
    print("✓ win32com.client imported successfully")
except ImportError as e:
    print(f"✗ win32com.client import failed: {e}")

try:
    import cv2
    print("✓ cv2 imported successfully")
except ImportError as e:
    print(f"✗ cv2 import failed: {e}")

try:
    import numpy
    print("✓ numpy imported successfully")
except ImportError as e:
    print(f"✗ numpy import failed: {e}")

try:
    import pdf2image
    print("✓ pdf2image imported successfully")
except ImportError as e:
    print(f"✗ pdf2image import failed: {e}")

try:
    import skimage
    print("✓ skimage imported successfully")
except ImportError as e:
    print(f"✗ skimage import failed: {e}")

try:
    import fitz  # PyMuPDF
    print("✓ PyMuPDF imported successfully")
except ImportError as e:
    print(f"✗ PyMuPDF import failed: {e}")

print("\nDependency check completed")