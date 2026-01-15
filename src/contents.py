from pathlib import Path

def upload_php_content() -> str:
    return r"""<?php
header('Content-Type: application/json');

$root = dirname(__DIR__, 2);
$blobRoot = $root . '/blob';
$metaRoot = $root . '/meta';
$envPath = $root . '/.env';

function respond_json($statusCode, $payload) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($payload);
    exit;
}

function load_config($envPath) {
    $defaultMaxMB = 5;
    $defaultExts = 'jpg,jpeg,png,webp,gif';
    $env = @parse_ini_file($envPath);
    $key = ($env && isset($env['HALAL_BLOB_KEY'])) ? trim($env['HALAL_BLOB_KEY']) : '';
    $baseUrl = ($env && isset($env['HALAL_BLOB_BASE_URL'])) ? rtrim(trim($env['HALAL_BLOB_BASE_URL']), '/') : '';
    $maxMB = ($env && isset($env['HALAL_BLOB_MAX_MB']) && is_numeric($env['HALAL_BLOB_MAX_MB'])) ? (float)$env['HALAL_BLOB_MAX_MB'] : $defaultMaxMB;
    $maxBytes = (int)round($maxMB * 1024 * 1024);
    $allowedExt = ($env && isset($env['HALAL_BLOB_ALLOWED_EXT']) && is_string($env['HALAL_BLOB_ALLOWED_EXT']) && strlen($env['HALAL_BLOB_ALLOWED_EXT']) > 0) ? $env['HALAL_BLOB_ALLOWED_EXT'] : $defaultExts;
    $allowedExts = array_map('strtolower', array_filter(array_map('trim', explode(',', $allowedExt))));
    return ['key' => $key, 'baseUrl' => $baseUrl, 'maxBytes' => $maxBytes, 'allowedExts' => $allowedExts];
}

function require_auth($expectedKey) {
    $headerKey = isset($_SERVER['HTTP_X_HALAL_BLOB_KEY']) ? trim($_SERVER['HTTP_X_HALAL_BLOB_KEY']) : '';
    $getKey = isset($_GET['key']) ? $_GET['key'] : '';
    $key = $headerKey !== '' ? $headerKey : $getKey;
    if ($expectedKey === '' || $key === '' || $key !== $expectedKey) {
        respond_json(403, ['success' => false, 'error' => ['code' => 'INVALID_KEY', 'message' => 'Forbidden']]);
    }
}

$cfg = load_config($envPath);
require_auth($cfg['key']);

if (!isset($_FILES['file']) || $_FILES['file']['error'] !== UPLOAD_ERR_OK) {
    respond_json(400, ['success' => false, 'error' => ['code' => 'NO_FILE', 'message' => 'No file uploaded']]);
}

$folder = isset($_POST['folder']) ? $_POST['folder'] : '';
$folder = trim($folder);
if ($folder !== '' && !preg_match('/^[A-Za-z0-9_\-\/]*$/', $folder)) {
    respond_json(400, ['success' => false, 'error' => ['code' => 'FOLDER_INVALID', 'message' => 'Folder contains invalid characters']]);
}
$folder = trim($folder, '/');

$targetDir = $blobRoot . ($folder ? ('/' . $folder) : '');
if (!is_dir($targetDir)) {
    if (!mkdir($targetDir, 0755, true)) {
        respond_json(500, ['success' => false, 'error' => ['code' => 'SERVER_ERROR', 'message' => 'Failed to create target directory']]);
    }
}

$originalName = $_FILES['file']['name'];
$ext = strtolower(pathinfo($originalName, PATHINFO_EXTENSION));
$sizeBytes = isset($_FILES['file']['size']) ? (int)$_FILES['file']['size'] : 0;
$tmpPath = $_FILES['file']['tmp_name'];

$finfo = finfo_open(FILEINFO_MIME_TYPE);
$realMime = finfo_file($finfo, $tmpPath);
finfo_close($finfo);

$mimeMap = [
    'jpg' => 'image/jpeg',
    'jpeg' => 'image/jpeg',
    'png' => 'image/png',
    'webp' => 'image/webp',
    'gif' => 'image/gif',
];

$allowedMimes = [];
foreach ($cfg['allowedExts'] as $e) {
    if (isset($mimeMap[$e])) { $allowedMimes[] = $mimeMap[$e]; }
}

if (!in_array($ext, $cfg['allowedExts'], true) || !in_array($realMime, $allowedMimes, true)) {
    respond_json(400, ['success' => false, 'error' => ['code' => 'INVALID_TYPE', 'message' => 'Unsupported file type']]);
}

if ($sizeBytes > $cfg['maxBytes']) {
    respond_json(400, ['success' => false, 'error' => ['code' => 'FILE_TOO_LARGE', 'message' => 'File exceeds maximum allowed size']]);
}

$basename = bin2hex(random_bytes(16));
$filename = $basename . ($ext ? ('.' . $ext) : '');
$targetPath = $targetDir . '/' . $filename;

if (!move_uploaded_file($_FILES['file']['tmp_name'], $targetPath)) {
    respond_json(500, ['success' => false, 'error' => ['code' => 'SERVER_ERROR', 'message' => 'Failed to save file']]);
}

$relativePath = ($folder ? ($folder . '/') : '') . $filename;
$baseUrl = $cfg['baseUrl'] ?: ('https://' . $_SERVER['HTTP_HOST']);
$url = $baseUrl . '/blob/' . $relativePath;

$meta = [
    'path' => $relativePath,
    'url' => $url,
    'size_bytes' => $sizeBytes,
    'mime_type' => $mime,
    'original_name' => $originalName,
    'uploaded_at' => gmdate('c'),
    'client_ip' => isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '',
    'folder' => $folder,
];

$metaDir = $metaRoot . ($folder ? ('/' . $folder) : '');
if (!is_dir($metaDir)) { mkdir($metaDir, 0755, true); }
$metaPath = $metaDir . '/' . $filename . '.json';
if (@file_put_contents($metaPath, json_encode($meta, JSON_PRETTY_PRINT)) === false) {
    respond_json(500, ['success' => false, 'error' => ['code' => 'SERVER_ERROR', 'message' => 'Failed to write metadata']]);
}

respond_json(200, [
    'success' => true,
    'url' => $url,
    'filename' => $filename,
    'path' => $relativePath,
    'meta' => [
        'size_bytes' => $sizeBytes,
        'mime_type' => $realMime,
        'uploaded_at' => $meta['uploaded_at'],
        'folder' => $folder,
        'original_name' => $originalName,
        'client_ip' => $meta['client_ip'],
    ],
]);
"""

def delete_php_content() -> str:
    return r"""<?php
header('Content-Type: application/json');

$root = dirname(__DIR__, 2);
$blobRoot = $root . '/blob';
$metaRoot = $root . '/meta';
$envPath = $root . '/.env';

function respond_json($statusCode, $payload) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($payload);
    exit;
}

function load_config($envPath) {
    $defaultMaxBytes = 5 * 1024 * 1024;
    $defaultExts = 'jpg,jpeg,png,webp,gif';
    $env = @parse_ini_file($envPath);
    $key = ($env && isset($env['HALAL_BLOB_KEY'])) ? trim($env['HALAL_BLOB_KEY']) : '';
    return ['key' => $key];
}

function require_auth($expectedKey) {
    $headerKey = isset($_SERVER['HTTP_X_HALAL_BLOB_KEY']) ? trim($_SERVER['HTTP_X_HALAL_BLOB_KEY']) : '';
    $getKey = isset($_GET['key']) ? $_GET['key'] : '';
    $key = $headerKey !== '' ? $headerKey : $getKey;
    if ($expectedKey === '' || $key === '' || $key !== $expectedKey) {
        respond_json(403, ['success' => false, 'error' => ['code' => 'INVALID_KEY', 'message' => 'Forbidden']]);
    }
}

$cfg = load_config($envPath);
require_auth($cfg['key']);

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data)) {
    respond_json(400, ['success' => false, 'error' => ['code' => 'SERVER_ERROR', 'message' => 'Invalid JSON']]);
}

$relativePath = '';
if (isset($data['path']) && is_string($data['path'])) {
    $relativePath = $data['path'];
} elseif (isset($data['filename']) && is_string($data['filename'])) {
    $relativePath = $data['filename'];
} else {
    respond_json(400, ['success' => false, 'error' => ['code' => 'SERVER_ERROR', 'message' => 'Missing path or filename']]);
}

$relativePath = preg_replace('/[^A-Za-z0-9_\-\.\/]/', '', $relativePath);
$relativePath = trim($relativePath, '/');

$fullPath = $blobRoot . '/' . $relativePath;
if (!is_file($fullPath)) {
    respond_json(404, ['success' => false, 'error' => ['code' => 'FILE_NOT_FOUND', 'message' => 'File not found']]);
}

if (!unlink($fullPath)) {
    respond_json(500, ['success' => false, 'error' => ['code' => 'DELETE_FAILED', 'message' => 'Failed to delete file']]);
}

$metaFull = $metaRoot . '/' . $relativePath . '.json';
if (is_file($metaFull)) { @unlink($metaFull); }

respond_json(200, ['success' => true]);
"""

def list_php_content() -> str:
    return r"""<?php
header('Content-Type: application/json');

$root = dirname(__DIR__, 2);
$blobRoot = $root . '/blob';
$metaRoot = $root . '/meta';
$envPath = $root . '/.env';

function respond_json($statusCode, $payload) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($payload);
    exit;
}

function load_config($envPath) {
    $defaultExts = 'jpg,jpeg,png,webp,gif';
    $env = @parse_ini_file($envPath);
    $key = ($env && isset($env['HALAL_BLOB_KEY'])) ? trim($env['HALAL_BLOB_KEY']) : '';
    return ['key' => $key];
}

function require_auth($expectedKey) {
    $headerKey = isset($_SERVER['HTTP_X_HALAL_BLOB_KEY']) ? trim($_SERVER['HTTP_X_HALAL_BLOB_KEY']) : '';
    $getKey = isset($_GET['key']) ? $_GET['key'] : '';
    $key = $headerKey !== '' ? $headerKey : $getKey;
    if ($expectedKey === '' || $key === '' || $key !== $expectedKey) {
        respond_json(403, ['success' => false, 'error' => ['code' => 'INVALID_KEY', 'message' => 'Forbidden']]);
    }
}

$cfg = load_config($envPath);
require_auth($cfg['key']);

$folder = isset($_GET['folder']) ? $_GET['folder'] : '';
$folder = trim($folder);
if ($folder !== '' && !preg_match('/^[A-Za-z0-9_\-\/]*$/', $folder)) {
    respond_json(400, ['success' => false, 'error' => ['code' => 'FOLDER_INVALID', 'message' => 'Invalid folder']]);
}
$folder = trim($folder, '/');

$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$perPage = isset($_GET['per_page']) ? (int)$_GET['per_page'] : 50;
if ($page < 1) { $page = 1; }
if ($perPage < 1) { $perPage = 50; }

$dir = $blobRoot . ($folder ? ('/' . $folder) : '');
if (!is_dir($dir)) {
    respond_json(400, ['success' => false, 'error' => ['code' => 'FOLDER_INVALID', 'message' => 'Folder not found']]);
}

$entries = scandir($dir);
$files = [];
foreach ($entries as $name) {
    if ($name === '.' || $name === '..') { continue; }
    $full = $dir . '/' . $name;
    if (!is_file($full)) { continue; }
    $relativePath = ($folder ? ($folder . '/') : '') . $name;
    $baseUrl = $cfg['baseUrl'] ?: ('https://' . $_SERVER['HTTP_HOST']);
    $url = $baseUrl . '/blob/' . $relativePath;
    $metaPath = $metaRoot . '/' . $relativePath . '.json';
    $meta = null;
    if (is_file($metaPath)) {
        $raw = @file_get_contents($metaPath);
        if ($raw !== false) {
            $dec = json_decode($raw, true);
            if (is_array($dec)) { $meta = $dec; }
        }
    }
    $files[] = ['path' => $relativePath, 'url' => $url, 'meta' => $meta];
}

usort($files, function($a, $b) { return strcmp($a['path'], $b['path']); });
$total = count($files);
$offset = ($page - 1) * $perPage;
if ($offset < 0) { $offset = 0; }
$paged = array_slice($files, $offset, $perPage);

respond_json(200, [
    'success' => true,
    'folder' => $folder,
    'page' => $page,
    'per_page' => $perPage,
    'total' => $total,
    'files' => $paged,
]);
"""

def ping_php_content() -> str:
    return r"""<?php
header('Content-Type: application/json');

$root = dirname(__DIR__, 2);
$envPath = $root . '/.env';

function respond_json($statusCode, $payload) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($payload);
    exit;
}

function load_config($envPath) {
    $env = @parse_ini_file($envPath);
    $key = ($env && isset($env['HALAL_BLOB_KEY'])) ? trim($env['HALAL_BLOB_KEY']) : '';
    return ['key' => $key];
}

function require_auth($expectedKey) {
    $headerKey = isset($_SERVER['HTTP_X_HALAL_BLOB_KEY']) ? trim($_SERVER['HTTP_X_HALAL_BLOB_KEY']) : '';
    $getKey = isset($_GET['key']) ? $_GET['key'] : '';
    $key = $headerKey !== '' ? $headerKey : $getKey;
    if ($expectedKey === '' || $key === '' || $key !== $expectedKey) {
        respond_json(403, ['success' => false, 'error' => ['code' => 'INVALID_KEY', 'message' => 'Forbidden']]);
    }
}

$cfg = load_config($envPath);
require_auth($cfg['key']);

respond_json(200, [
    'success' => true,
    'status' => 'ok',
    'php_version' => PHP_VERSION,
    'time' => gmdate('c'),
]);
"""

def env_template_content() -> str:
    return (
        "HALAL_BLOB_KEY=\"REPLACE_WITH_A_RANDOM_64_CHAR_SECRET\"\n"
        "HALAL_BLOB_BASE_URL=\"https://blob.yourdomain.com\"\n"
        "HALAL_BLOB_MAX_MB=\"5\"\n"
        "HALAL_BLOB_ALLOWED_EXT=\"jpg,jpeg,png,webp,gif\"\n"
    )

def howto_txt_content() -> str:
    return (
        "1) Setup\n"
        "- Upload & Unzip to public_html/ (or subfolder).\n"
        "- Point subdomain (e.g. blob.yourdomain.com) to this folder.\n\n"
        "2) Config\n"
        "- Rename .env-template to .env\n"
        "  (NOTE: In cPanel File Manager, click 'Settings' (top right) -> Check 'Show Hidden Files' to see .env!)\n"
        "- Edit .env: Set HALAL_BLOB_KEY (random string) and HALAL_BLOB_BASE_URL.\n\n"
        "3) Usage\n"
        "- Use the SDK (sdk/node/halalBlobClient.ts) in your App.\n"
        "- Pass env vars: HALAL_BLOB_KEY, HALAL_BLOB_BASE_URL.\n"
    )

def api_htaccess_content() -> str:
    return (
        "Options -Indexes\n"
        "<FilesMatch \\.(env|ini)$>\n"
        "  Require all denied\n"
        "</FilesMatch>\n"
    )

def blob_htaccess_content() -> str:
    return (
        "Options -Indexes\n"
        "<FilesMatch \\.(php)$>\n"
        "  Require all denied\n"
        "</FilesMatch>\n"
    )

