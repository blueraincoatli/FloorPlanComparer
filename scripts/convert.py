from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _default_converter() -> str | None:
    env_value = os.getenv("FLOORPLAN_CONVERTER_PATH")
    if env_value:
        return env_value
    default_path = Path("/opt/oda/ODAFileConverter.exe")
    if sys.platform == "win32":
        default_path = Path("C:/Program Files/ODA/ODAFileConverter 26.9.0/ODAFileConverter.exe")
    return str(default_path)


def _default_input_dir() -> str:
    env_value = os.getenv("FLOORPLAN_CONVERTER_INPUT")
    if env_value:
        return env_value
    return str(Path("originFile").resolve())


def _default_output_dir() -> str:
    env_value = os.getenv("FLOORPLAN_CONVERTER_OUTPUT")
    if env_value:
        return env_value
    storage_root = Path(os.getenv("FLOORPLAN_STORAGE_DIR", "storage"))
    return str((storage_root / "temp").resolve())


def _resolve_converter(path: Path) -> Path:
    if path.exists():
        return path
    if sys.platform == "win32" and path.suffix.lower() != ".exe":
        candidate = path.with_suffix(".exe")
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Converter executable not found at {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ODA File Converter with project defaults")
    parser.add_argument("--converter", default=_default_converter(), help="Absolute path to the ODA File Converter executable")
    parser.add_argument("--input", default=_default_input_dir(), help="Directory containing source DWG files")
    parser.add_argument("--output", default=_default_output_dir(), help="Directory where converted files will be written")
    parser.add_argument("--acad-version", default="ACAD2018", help="Target AutoCAD version (e.g. ACAD2018)")
    parser.add_argument("--target-format", default="DXF", choices=["DXF", "DWG"], help="Target output format")
    parser.add_argument("--recursive", action="store_true", help="Recurse into subdirectories when converting")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false", help="Do not recurse (default)")
    parser.add_argument("--audit", dest="audit", action="store_true", help="Run audit during conversion (default)")
    parser.add_argument("--no-audit", dest="audit", action="store_false", help="Skip audit during conversion")
    parser.set_defaults(recursive=False, audit=True)

    args = parser.parse_args(argv)

    converter_path = _resolve_converter(Path(args.converter).expanduser())
    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()

    if not input_dir.exists():
        parser.error(f"Input directory does not exist: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(converter_path),
        str(input_dir),
        str(output_dir),
        args.acad_version,
        args.target_format,
        "1" if args.recursive else "0",
        "1" if args.audit else "0",
    ]

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except subprocess.CalledProcessError as exc:
        print(f"Converter exited with error code {exc.returncode}", file=sys.stderr)
        return exc.returncode

    print(f"Conversion completed. Output written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
