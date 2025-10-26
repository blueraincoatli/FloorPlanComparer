
import sys
import ezdxf
from ezdxf import bbox
from pathlib import Path
import re
from collections import defaultdict

def analyze_dxf(file_path: str):
    """
    Analyzes a DXF file to find potential architectural grid systems (axes).
    """
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
    except Exception as e:
        print(f"Error reading DXF file: {e}")
        return

    # --- 1. List all layers ---
    print("--- Layers ---")
    for layer in doc.layers:
        print(f"- {layer.dxf.name}")

    # --- 2. Find potential grid labels (Text inside Circles) ---
    print("\n--- Potential Grid Labels (Text in Circles) ---")
    texts = msp.query("TEXT MTEXT")
    circles = msp.query("CIRCLE")
    
    # A simple spatial index for circles
    circle_index = defaultdict(list)
    for circle in circles:
        # Group circles by their center y-coordinate for horizontal axes, x for vertical
        # This is a heuristic
        key_x = round(circle.dxf.center.x / 1000) # Grouping by meter for typical scales
        key_y = round(circle.dxf.center.y / 1000)
        circle_index[f"x:{key_x}"].append(circle)
        circle_index[f"y:{key_y}"].append(circle)

    grid_labels = []
    # Regex for typical axis labels (e.g., A, B, 1, 2, A', 1')
    label_pattern = re.compile(r"^\s*([A-Z]{1,2}|\d{1,3})'??\s*$")

    for text in texts:
        content = text.dxf.text if text.dxftype() == 'TEXT' else text.text
        if label_pattern.match(content):
            is_in_circle = False
            for circle in circles:
                # Check if text center is inside the circle's bounding box
                if circle.dxf.radius > 0 and \
                   (text.dxf.insert - circle.dxf.center).magnitude < circle.dxf.radius:
                    is_in_circle = True
                    break
            if is_in_circle:
                grid_labels.append((content, text.dxf.layer))

    if grid_labels:
        for label, layer in sorted(list(set(grid_labels))):
            print(f"- Found Label: \"{label}\" on Layer: \"{layer}\"")
    else:
        print("No text entities found inside circles.")


    print("\n--- Brute-force Search for All Line-like Entities ---")
    all_line_entities = msp.query('LINE LWPOLYLINE POLYLINE XLINE RAY')
    
    def get_entity_length(entity):
        if entity.dxftype() in ('XLINE', 'RAY'):
            return float('inf') # Construction lines are infinite
        if entity.dxftype() == 'LINE':
            return (entity.dxf.end - entity.dxf.start).magnitude
        elif hasattr(entity, 'length'):
            return entity.length
        return 0

    entity_details = []
    for entity in all_line_entities:
        length = get_entity_length(entity)
        entity_details.append((entity.dxftype(), entity.dxf.layer, length))

    # Sort by length descending to see the longest lines first
    entity_details.sort(key=lambda x: x[2], reverse=True)

    print(f"Found {len(entity_details)} total line-like entities. Showing top 20 longest:")
    for i, (etype, layer, length) in enumerate(entity_details[:20]):
        print(f"- #{i+1}: Type={etype}, Layer='{layer}', Length={length:.2f}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_dxf_axes.py <path_to_dxf_file>")
    else:
        file = Path(sys.argv[1])
        if not file.exists():
            print(f"File not found: {file}")
        else:
            analyze_dxf(sys.argv[1])
