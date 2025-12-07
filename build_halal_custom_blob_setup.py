# Recommended: run with `uv run this_script.py`
# Fallback:     `python this_script.py`

from pathlib import Path
import os
import src.contents as contents
from src.build_ops import create_directories, write_files, create_zip
from src.sdk_writer import write_sdk
from src import __version__

ZIP_NAME = "halal-custom-blob-setup.zip"


def main() -> None:
    base_path = Path.cwd() / "halal_custom_blob_setup_build"
    print(f"Building Halal Custom Blob Setup v{__version__}...")
    create_directories(base_path)
    write_files(base_path)
    create_zip(base_path, ZIP_NAME)
    write_sdk(Path.cwd())

    zip_path = Path.cwd() / ZIP_NAME
    if not zip_path.exists():
        raise FileNotFoundError(f"{ZIP_NAME} missing at {zip_path}")

    print(f"ZIP READY! {ZIP_NAME}")


if __name__ == "__main__":
    main()
