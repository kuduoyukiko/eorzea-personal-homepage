# -*- coding: utf-8 -*-
import os
import uuid
from flask import current_app, send_file

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

# 缩略图配置
THUMBNAIL_MAX_WIDTH = 800
THUMBNAIL_MAX_HEIGHT = 600
THUMBNAIL_SUFFIX = "_thumb"


def get_upload_folder():
    """获取本地上传目录的绝对路径"""
    folder = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(folder, exist_ok=True)
    return folder


def _get_thumbnail_path(file_path):
    """根据原始文件路径获取缩略图路径"""
    root, ext = os.path.splitext(file_path)
    return root + THUMBNAIL_SUFFIX + ext


def _is_image_ext(filename):
    """判断文件扩展名是否为图片"""
    image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    ext = os.path.splitext(filename)[1].lower()
    return ext in image_exts


def save_real_life_photo(file_storage):
    """Normalize a public real-life photo and remove embedded EXIF metadata.

    Photos are always stored as WebP: this removes camera metadata (including
    location) and avoids serving original full-resolution phone files.
    """
    from PIL import Image, ImageOps, UnidentifiedImageError

    original_filename = file_storage.filename or "photo"
    extension = os.path.splitext(original_filename)[1].lower()
    supported = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
    if extension not in supported:
        raise ValueError("请选择 JPG、PNG、WebP 或 HEIC/HEIF 图片。")
    if extension in {".heic", ".heif"} and not HEIF_AVAILABLE:
        raise ValueError("服务器尚未启用 HEIC/HEIF 解码，请安装 pillow-heif 后重试。")

    try:
        image = Image.open(file_storage.stream)
        image.verify()
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream)
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        if image.mode == "RGBA":
            canvas = Image.new("RGB", image.size, "#10192b")
            canvas.paste(image, mask=image.getchannel("A"))
            image = canvas

        upload_folder = get_upload_folder()
        unique_name = f"life-{uuid.uuid4().hex}.webp"
        file_path = os.path.join(upload_folder, unique_name)
        image.save(file_path, "WEBP", quality=88, method=6)
        _generate_thumbnail(file_path)
        return file_path, f"/static/uploads/{unique_name}", unique_name
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ValueError("无法读取这张照片，请换一张原始图片后重试。") from error


def _generate_thumbnail(file_path):
    """生成缩略图，返回缩略图路径（如果生成失败返回None）"""
    thumb_path = _get_thumbnail_path(file_path)
    if os.path.exists(thumb_path):
        return thumb_path  # 已存在则跳过

    try:
        from PIL import Image
        img = Image.open(file_path)
        # 计算缩放尺寸，保持宽高比
        img.thumbnail((THUMBNAIL_MAX_WIDTH, THUMBNAIL_MAX_HEIGHT), Image.LANCZOS)

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGBA')
        img.save(thumb_path, quality=85, optimize=True)
        return thumb_path
    except Exception as e:
        print(f"生成缩略图失败: {e}")
        return None


def save_uploaded_file(file_storage):
    """
    将上传的文件保存到本地 static/uploads/ 目录
    自动为图片生成缩略图
    返回: (本地文件路径, URL路径, 唯一文件名)
    """
    upload_folder = get_upload_folder()

    # 生成唯一文件名，保留原扩展名
    original_filename = file_storage.filename or "file"
    ext = os.path.splitext(original_filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"

    # 保存文件
    file_path = os.path.join(upload_folder, unique_name)
    file_storage.save(file_path)

    # 如果是图片，生成缩略图
    if _is_image_ext(unique_name):
        _generate_thumbnail(file_path)

    # URL 路径 (Flask 的 static 映射)
    url_path = f"/static/uploads/{unique_name}"

    return file_path, url_path, unique_name


def get_thumbnail_url(url_path):
    """
    根据原图URL获取缩略图URL
    e.g. /static/uploads/abc.png -> /static/uploads/abc_thumb.png
    """
    if not url_path:
        return url_path
    filename = os.path.basename(url_path)
    root, ext = os.path.splitext(filename)
    return f"/static/uploads/{root}{THUMBNAIL_SUFFIX}{ext}"


def serve_thumbnail(filename):
    """
    提供缩略图服务：
    1. 如果传入的文件名已有 _thumb 后缀，直接返回该文件
    2. 如果缩略图已存在，直接返回
    3. 如果原图存在但无缩略图，即时生成并返回
    4. 都不存在返回 None
    """
    upload_folder = get_upload_folder()
    
    # 如果文件名已有 _thumb 后缀，直接 serve（避免 _thumb_thumb 嵌套）
    if THUMBNAIL_SUFFIX in filename:
        file_path = os.path.join(upload_folder, filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype=_guess_mime(filename))
        return None
    
    # 普通文件名：查找/生成缩略图
    file_path = os.path.join(upload_folder, filename)
    thumb_path = _get_thumbnail_path(file_path)
    
    # 如果缩略图已有，直接返回
    if os.path.exists(thumb_path):
        return send_file(thumb_path, mimetype=_guess_mime(filename))
    
    # 如果原图存在，生成缩略图再返回
    if os.path.exists(file_path) and _is_image_ext(filename):
        thumb_path = _generate_thumbnail(file_path)
        if thumb_path and os.path.exists(thumb_path):
            return send_file(thumb_path, mimetype=_guess_mime(filename))
    
    return None


def _guess_mime(filename):
    """简单猜测MIME类型"""
    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.ogg': 'video/ogg',
        '.mov': 'video/quicktime',
    }
    return mime_map.get(ext, 'application/octet-stream')


def delete_local_file(url_path):
    """
    根据 URL 路径删除本地文件及缩略图
    url_path 格式: /static/uploads/filename.ext
    返回: bool (成功/失败)
    """
    if not url_path:
        return False

    filename = os.path.basename(url_path)
    upload_folder = get_upload_folder()
    file_path = os.path.join(upload_folder, filename)
    thumb_path = _get_thumbnail_path(file_path)

    deleted = False
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted = True
        # 同时删除缩略图
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
        return deleted
    except Exception as e:
        print(f"删除文件失败: {e}")
        return False


def get_local_url(filename):
    """根据文件名生成本地 URL 路径"""
    return f"/static/uploads/{filename}"


def list_local_files():
    """列出 static/uploads 下的所有文件"""
    upload_folder = get_upload_folder()
    files = []
    try:
        for fname in os.listdir(upload_folder):
            # 跳过缩略图
            if THUMBNAIL_SUFFIX in fname:
                continue
            file_path = os.path.join(upload_folder, fname)
            if os.path.isfile(file_path):
                ext = os.path.splitext(fname)[1].lower()
                thumb_path = _get_thumbnail_path(file_path)
                files.append({
                    "filename": fname,
                    "url": get_local_url(fname),
                    "thumb_url": get_local_url(os.path.basename(thumb_path)) if os.path.exists(thumb_path) else get_local_url(fname),
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "ext": ext,
                    "mtime": os.path.getmtime(file_path),
                })
    except Exception as e:
        print(f"列出本地文件失败: {e}")

    # 按修改时间倒序
    files.sort(key=lambda f: f["mtime"], reverse=True)
    return files


def batch_generate_thumbnails():
    """
    批量生成所有图片的缩略图
    返回: (成功数, 失败数)
    """
    upload_folder = get_upload_folder()
    success = 0
    failed = 0
    try:
        for fname in os.listdir(upload_folder):
            if THUMBNAIL_SUFFIX in fname:
                continue  # 跳过已经是缩略图的文件
            if not _is_image_ext(fname):
                continue  # 跳过非图片文件
            file_path = os.path.join(upload_folder, fname)
            if os.path.isfile(file_path):
                try:
                    thumb_path = _generate_thumbnail(file_path)
                    if thumb_path:
                        success += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
    except Exception as e:
        print(f"批量生成缩略图出错: {e}")
    return success, failed

