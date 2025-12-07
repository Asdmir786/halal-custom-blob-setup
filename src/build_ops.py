from pathlib import Path
import zipfile
from .contents import (
    env_template_content,
    api_htaccess_content,
    blob_htaccess_content,
    upload_php_content,
    delete_php_content,
    list_php_content,
    ping_php_content,
    howto_txt_content,
)

def create_directories(base_path: Path) -> None:
    (base_path / "api" / "blob").mkdir(parents=True, exist_ok=True)
    (base_path / "blob").mkdir(parents=True, exist_ok=True)
    (base_path / "meta").mkdir(parents=True, exist_ok=True)

def write_files(base_path: Path) -> None:
    (base_path / ".env-template").write_text(env_template_content(), encoding="utf-8")
    (base_path / "api" / ".htaccess").write_text(api_htaccess_content(), encoding="utf-8")
    (base_path / "blob" / ".htaccess").write_text(blob_htaccess_content(), encoding="utf-8")
    (base_path / "api" / "blob" / "upload.php").write_text(upload_php_content(), encoding="utf-8")
    (base_path / "api" / "blob" / "delete.php").write_text(delete_php_content(), encoding="utf-8")
    (base_path / "api" / "blob" / "list.php").write_text(list_php_content(), encoding="utf-8")
    (base_path / "api" / "blob" / "ping.php").write_text(ping_php_content(), encoding="utf-8")
    (base_path / "How to Setup [EZ].txt").write_text(howto_txt_content(), encoding="utf-8")

def create_zip(base_path: Path, zip_name: str) -> None:
    with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(base_path / "api" / ".htaccess", arcname="api/.htaccess")
        zf.write(base_path / "api" / "blob" / "upload.php", arcname="api/blob/upload.php")
        zf.write(base_path / "api" / "blob" / "delete.php", arcname="api/blob/delete.php")
        zf.write(base_path / "api" / "blob" / "list.php", arcname="api/blob/list.php")
        zf.write(base_path / "api" / "blob" / "ping.php", arcname="api/blob/ping.php")
        zf.write(base_path / "blob" / ".htaccess", arcname="blob/.htaccess")
        zf.write(base_path / ".env-template", arcname=".env-template")
        zf.write(base_path / "How to Setup [EZ].txt", arcname="How to Setup [EZ].txt")

        info_blob = zipfile.ZipInfo("blob/")
        info_blob.external_attr = 0o755 << 16
        zf.writestr(info_blob, "")

        info_meta = zipfile.ZipInfo("meta/")
        info_meta.external_attr = 0o755 << 16
        zf.writestr(info_meta, "")

