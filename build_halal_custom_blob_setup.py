# Recommended: run with `uv run this_script.py`
# Fallback:     `python this_script.py`

from pathlib import Path
import zipfile

ZIP_NAME = "halal-custom-blob-setup.zip"


def create_directories(base_path: Path) -> None:
    (base_path / "api" / "blob").mkdir(parents=True, exist_ok=True)
    (base_path / "blob").mkdir(parents=True, exist_ok=True)


def upload_php_content() -> str:
    return (
        "<?php\n"
        "header('Content-Type: application/json');\n\n"
        "$root = dirname(__DIR__, 2);\n"
        "$envPath = $root . '/.env';\n"
        "$config = parse_ini_file($envPath);\n\n"
        "$expectedKey = isset($config['HALAL_BLOB_KEY']) ? $config['HALAL_BLOB_KEY'] : null;\n"
        "$key = isset($_GET['key']) ? $_GET['key'] : null;\n\n"
        "if (!$expectedKey || !$key || $key !== $expectedKey) {\n"
        "    http_response_code(403);\n"
        "    echo json_encode(['error' => 'Forbidden']);\n"
        "    exit;\n"
        "}\n\n"
        "if (!isset($_FILES['file']) || $_FILES['file']['error'] !== UPLOAD_ERR_OK) {\n"
        "    http_response_code(400);\n"
        "    echo json_encode(['error' => 'No file uploaded']);\n"
        "    exit;\n"
        "}\n\n"
        "$folder = isset($_POST['folder']) ? $_POST['folder'] : '';\n"
        "$folder = preg_replace('/[^A-Za-z0-9_\\-\\\/]/', '', $folder);\n"
        "$folder = trim($folder, '/');\n\n"
        "$blobRoot = $root . '/blob';\n"
        "$targetDir = $blobRoot . ($folder ? ('/' . $folder) : '');\n\n"
        "if (!is_dir($targetDir)) {\n"
        "    mkdir($targetDir, 0755, true);\n"
        "}\n\n"
        "$originalName = $_FILES['file']['name'];\n"
        "$ext = strtolower(pathinfo($originalName, PATHINFO_EXTENSION));\n"
        "$basename = bin2hex(random_bytes(16));\n"
        "$filename = $basename . ($ext ? ('.' . $ext) : '');\n\n"
        "$finfo = finfo_open(FILEINFO_MIME_TYPE);\n"
        "$mime = finfo_file($finfo, $_FILES['file']['tmp_name']);\n"
        "finfo_close($finfo);\n\n"
        "$allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];\n"
        "if (!in_array($mime, $allowed, true)) {\n"
        "    http_response_code(400);\n"
        "    echo json_encode(['error' => 'Unsupported file type']);\n"
        "    exit;\n"
        "}\n\n"
        "$finalPath = $targetDir . '/' . $filename;\n"
        "if (!move_uploaded_file($_FILES['file']['tmp_name'], $finalPath)) {\n"
        "    http_response_code(500);\n"
        "    echo json_encode(['error' => 'Failed to save file']);\n"
        "    exit;\n"
        "}\n\n"
        "$relativePath = ($folder ? ($folder . '/') : '') . $filename;\n"
        "$url = 'https://blob.yourdomain.com/blob/' . $relativePath;\n\n"
        "echo json_encode([\n"
        "    'success' => true,\n"
        "    'url' => $url,\n"
        "    'filename' => $filename,\n"
        "    'path' => $relativePath\n"
        "]);\n"
    )


def delete_php_content() -> str:
    return (
        "<?php\n"
        "header('Content-Type: application/json');\n\n"
        "$root = dirname(__DIR__, 2);\n"
        "$envPath = $root . '/.env';\n"
        "$config = parse_ini_file($envPath);\n\n"
        "$expectedKey = isset($config['HALAL_BLOB_KEY']) ? $config['HALAL_BLOB_KEY'] : null;\n"
        "$key = isset($_GET['key']) ? $_GET['key'] : null;\n\n"
        "if (!$expectedKey || !$key || $key !== $expectedKey) {\n"
        "    http_response_code(403);\n"
        "    echo json_encode(['error' => 'Forbidden']);\n"
        "    exit;\n"
        "}\n\n"
        "$raw = file_get_contents('php://input');\n"
        "$data = json_decode($raw, true);\n\n"
        "if (!is_array($data)) {\n"
        "    http_response_code(400);\n"
        "    echo json_encode(['error' => 'Invalid JSON']);\n"
        "    exit;\n"
        "}\n\n"
        "$relativePath = '';\n\n"
        "if (isset($data['path']) && is_string($data['path'])) {\n"
        "    $relativePath = $data['path'];\n"
        "} elseif (isset($data['filename']) && is_string($data['filename'])) {\n"
        "    $relativePath = $data['filename'];\n"
        "} else {\n"
        "    http_response_code(400);\n"
        "    echo json_encode(['error' => 'Missing path or filename']);\n"
        "    exit;\n"
        "}\n\n"
        "$relativePath = preg_replace('/[^A-Za-z0-9_\\-\.\\\/]/', '', $relativePath);\n"
        "$relativePath = trim($relativePath, '/');\n\n"
        "$blobRoot = $root . '/blob';\n"
        "$fullPath = $blobRoot . '/' . $relativePath;\n\n"
        "if (!is_file($fullPath)) {\n"
        "    http_response_code(404);\n"
        "    echo json_encode(['error' => 'File not found']);\n"
        "    exit;\n"
        "}\n\n"
        "if (!unlink($fullPath)) {\n"
        "    http_response_code(500);\n"
        "    echo json_encode(['error' => 'Failed to delete file']);\n"
        "    exit;\n"
        "}\n\n"
        "echo json_encode(['success' => true]);\n"
    )


def env_template_content() -> str:
    return "HALAL_BLOB_KEY=REPLACE_WITH_A_RANDOM_64_CHAR_SECRET\n"


def howto_txt_content() -> str:
    return (
        "Setup\n"
        "- Rename .env-template to .env.\n"
        "- Set HALAL_BLOB_KEY to a 64–128 char secret (no spaces).\n\n"
        "Upload\n"
        "- POST /api/blob/upload.php?key=YOUR_SECRET_KEY\n"
        "- Body: multipart/form-data (file, optional folder).\n"
        "- Returns JSON with url and path.\n\n"
        "Delete\n"
        "- POST /api/blob/delete.php?key=YOUR_SECRET_KEY\n"
        "- Body: JSON { \"path\": \"subfolder/filename.ext\" } (or just filename).\n"
        "- Returns { \"success\": true }.\n"
    )


def write_files(base_path: Path) -> None:
    (base_path / ".env-template").write_text(env_template_content(), encoding="utf-8")
    (base_path / "api" / "blob" / "upload.php").write_text(upload_php_content(), encoding="utf-8")
    (base_path / "api" / "blob" / "delete.php").write_text(delete_php_content(), encoding="utf-8")
    (base_path / "How to Setup [EZ].txt").write_text(howto_txt_content(), encoding="utf-8")


def create_zip(base_path: Path) -> None:
    with zipfile.ZipFile(ZIP_NAME, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(base_path / "api" / "blob" / "upload.php", arcname="api/blob/upload.php")
        zf.write(base_path / "api" / "blob" / "delete.php", arcname="api/blob/delete.php")
        zf.write(base_path / ".env-template", arcname=".env-template")
        zf.write(base_path / "How to Setup [EZ].txt", arcname="How to Setup [EZ].txt")

        info = zipfile.ZipInfo("blob/")
        info.external_attr = 0o755 << 16
        zf.writestr(info, "")


def main() -> None:
    base_path = Path.cwd() / "halal_custom_blob_setup_build"
    create_directories(base_path)
    write_files(base_path)
    create_zip(base_path)
    print(f"ZIP READY! {ZIP_NAME}")


if __name__ == "__main__":
    main()
