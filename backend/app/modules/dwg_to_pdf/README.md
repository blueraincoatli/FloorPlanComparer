# DWG to PDF Converter Module

## Overview
This module provides functionality to convert DWG files to PDF format. Due to limitations in available Python libraries for directly reading DWG files, this implementation currently creates placeholder PDFs with file information.

## Current Implementation
The current implementation creates placeholder PDFs containing:
- File name
- File size
- File path
- Timestamp of conversion
- A note about the limitation

## Future Improvements
To implement actual DWG to PDF conversion, the following approaches could be considered:

1. **Using external tools**: Integrate with command-line tools like LibreCAD's dxflib or QCAD's command-line interface
2. **Commercial libraries**: Use commercial libraries that support DWG format reading
3. **Two-step conversion**: Convert DWG to DXF first (using external tools), then process the DXF with ezdxf

## Usage
```python
from modules.dwg_to_pdf.converter import DWGToPDFConverter

converter = DWGToPDFConverter()
success = converter.convert(
    input_path="path/to/input.dwg",
    output_path="path/to/output.pdf",
    auto_fit=True,
    center=True
)
```

## Dependencies
- reportlab: For PDF generation
- ezdxf: For potential future DXF processing (currently not used for DWG reading)

## Limitations
- Cannot directly read DWG files due to format restrictions
- Creates placeholder PDFs instead of actual conversions
- Requires external tools or commercial libraries for full functionality