# app.py
import os
import re

# 允许显示的文件扩展名（图片和视频）
ALLOWED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".mp4",
    ".webm",
    ".ogg",
    ".mov",
    ".webp",
    ".heic",
    ".heif",
}
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
    make_response,
    Blueprint,
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.utils import secure_filename
from utils.email_notifications import queue_new_message_notification
from markupsafe import Markup, escape

from config import Config
from utils import data_utils, local_storage_utils

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB

# 确保数据目录存在
os.makedirs(app.config["DATA_PATH"], exist_ok=True)

# 确保本地临时上传目录存在（可选，用于COS上传前暂存）
UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

EMOTE_PATTERN = re.compile(r"\[emote:(\d{6})\]")
EMOTE_IDS = tuple(sorted(
    filename.removesuffix("_hr1.png")
    for filename in os.listdir(os.path.join(app.static_folder, "images", "emotes"))
    if re.fullmatch(r"\d{6}_hr1\.png", filename)
))
EMOTE_ID_SET = frozenset(EMOTE_IDS)
COMMON_EMOTE_IDS = tuple(emote_id for emote_id in (
    "064001", "064002", "064003", "064004", "064007", "064010", "064013", "064017",
    "064020", "064021", "064023", "064024", "064026", "064029", "064032", "064034",
    "064040", "064042", "064043", "064044", "064049", "064053", "064060", "064064",
    "064069", "064070", "064071", "064072", "064074", "064077", "064078", "064079",
    "064082", "064089", "064091", "064103", "064107", "064114", "064125", "064133",
) if emote_id in EMOTE_ID_SET)


def validate_emote_content(content):
    """只接受现有表情，并限制每段内容最多插入十个。"""
    emote_ids = EMOTE_PATTERN.findall(content or "")
    return len(emote_ids) <= 10 and all(emote_id in EMOTE_ID_SET for emote_id in emote_ids)


@app.template_filter("render_message")
def render_message(content):
    """安全渲染留言文字与服务端白名单内的情感动作图标。"""
    content = content or ""
    output = []
    cursor = 0
    for match in EMOTE_PATTERN.finditer(content):
        output.append(str(escape(content[cursor:match.start()])).replace("\n", "<br>"))
        emote_id = match.group(1)
        if emote_id in EMOTE_ID_SET:
            src = url_for("static", filename=f"images/emotes/{emote_id}_hr1.png")
            output.append(
                f'<img class="message-emote" src="{escape(src)}" alt="情感动作 {emote_id}" '
                'width="32" height="32" loading="lazy">'
            )
        else:
            output.append(str(escape(match.group(0))))
        cursor = match.end()
    output.append(str(escape(content[cursor:])).replace("\n", "<br>"))
    return Markup("".join(output))


@app.context_processor
def inject_asset_helpers():
    """为本地静态资源附加内容更新时间，避免部署后命中旧缓存。"""

    def versioned_static(filename):
        static_path = os.path.join(app.static_folder, *filename.split("/"))
        try:
            version = str(os.stat(static_path).st_mtime_ns)
        except OSError:
            version = "0"
        return url_for("static", filename=filename, v=version)

    return {
        "versioned_static": versioned_static,
        "emote_ids": EMOTE_IDS,
        "common_emote_ids": COMMON_EMOTE_IDS,
        "site_mode": app.config["SITE_MODE"],
        "visible_character_count": 1 if app.config["SITE_MODE"] == "single" else 2,
    }

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin.login"


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    if user_id == app.config["ADMIN_USERNAME"]:
        return User(user_id)
    return None


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated_function


# ---------- 公共页面路由 ----------
@app.route("/")
def index():
    # 增加浏览量
    site_config = data_utils.read_json("site_config.json")
    site_config["views"] = site_config.get("views", 0) + 1
    data_utils.write_json("site_config.json", site_config)

    home_data = data_utils.read_json("home.json")
    messages = data_utils.read_json("messages.json") or []
    recent_messages = list(reversed(messages[-2:]))
    # 传递数据到模板
    return render_template(
        "index.html",
        home=home_data,
        recent_messages=recent_messages,
        site_config=site_config,
    )


@app.route("/characters")
def characters():
    chars = data_utils.read_json("characters.json")
    intro = data_utils.read_json("intro.json")
    site_config = data_utils.read_json("site_config.json")
    return render_template(
        "characters.html", characters=chars, intro=intro, site_config=site_config
    )


@app.route("/jobs")
def jobs():
    jobs_data = data_utils.read_json("jobs.json")
    site_config = data_utils.read_json("site_config.json")
    return render_template("jobs.html", jobs=jobs_data, site_config=site_config)


@app.route('/gallery')
def gallery():
    gallery_data = data_utils.read_json('gallery.json') or []
    # 只保留 show 为 true 的文件
    filtered = [item for item in gallery_data if item.get('show', True)]
    
    # 分组
    acc1 = []
    acc2 = []
    both = []
    for item in filtered:
        # 为每个图片添加缩略图URL
        url = item.get('url', '')
        if url and local_storage_utils._is_image_ext(os.path.basename(url)):
            item['thumb_url'] = local_storage_utils.get_thumbnail_url(url)
        else:
            item['thumb_url'] = url
        acc = item.get('account', '1')  # 默认账号1（兼容旧数据）
        if acc == '1':
            acc1.append(item)
        elif acc == '2':
            acc2.append(item)
        else:
            both.append(item)
    
    # 排序：置顶优先，然后按上传时间倒序（如果有 upload_time 字段）
    def sort_key(item):
        sticky = 0 if item.get('sticky') else 1
        time = item.get('upload_time', '')
        return (sticky, time)
    
    acc1.sort(key=sort_key)
    acc2.sort(key=sort_key)
    both.sort(key=sort_key)
    
    site_config = data_utils.read_json('site_config.json')
    return render_template('gallery.html', acc1=acc1, acc2=acc2, both=both, site_config=site_config)


@app.route("/social")
def social():
    social_links = data_utils.read_json("social.json")
    intro = data_utils.read_json("intro.json")
    life_photos = data_utils.read_json("real_life_photos.json") or []
    life_photos = [photo for photo in life_photos if photo.get("show", True)]
    for photo in life_photos:
        photo["thumb_url"] = local_storage_utils.get_thumbnail_url(photo.get("url", ""))
    life_photos.sort(key=lambda photo: photo.get("upload_time", ""), reverse=True)
    site_config = data_utils.read_json("site_config.json")
    return render_template(
        "social.html",
        social=social_links,
        intro=intro,
        life_photos=life_photos,
        life_categories={"daily": "日常", "travel": "旅行", "food": "美食"},
        site_config=site_config,
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        game_id = request.form.get("game_id")
        server = request.form.get("server")
        content = request.form.get("content")

        if game_id and server and content and validate_emote_content(content):
            name = f"{game_id}@{server}"  # 组合成“ID@服务器”格式
            messages = data_utils.read_json("messages.json")
            message_data = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "content": content,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "replies": [],
                }
            messages.append(message_data)
            data_utils.write_json("messages.json", messages)
            site_url = app.config.get("SITE_URL") or request.url_root.rstrip("/")
            queue_new_message_notification(
                app, message_data, f"{site_url}{url_for('admin.messages')}"
            )
            flash("留言已提交，等待管理员回复", "success")
        elif content and not validate_emote_content(content):
            flash("每条留言最多使用 10 个有效的情感动作", "danger")
        else:
            flash("请填写完整的游戏ID、服务器和留言内容", "danger")
        return redirect(url_for("contact"))

    messages = data_utils.read_json("messages.json")
    site_config = data_utils.read_json("site_config.json")
    return render_template("contact.html", messages=messages, site_config=site_config)


# ---------- 管理员蓝图 ----------
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if (
            username == app.config["ADMIN_USERNAME"]
            and password == app.config["ADMIN_PASSWORD"]
        ):
            user = User(username)
            session.clear()
            login_user(user, remember=False, fresh=True)
            session.permanent = False
            return redirect(url_for("admin.dashboard"))
        else:
            flash("用户名或密码错误", "danger")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    return redirect(url_for("admin.signout_v3"), code=303)


@admin_bp.route("/signout-v2", methods=["GET", "POST"])
def signout_v2():
    return redirect(url_for("admin.signout_v3"), code=303)


@admin_bp.route("/signout-v3", methods=["GET", "POST"])
def signout_v3():
    logout_user()
    session.clear()
    response = make_response(render_template("admin/signed_out.html"))
    # Delete both current and legacy auth cookies explicitly. This remains
    # effective even if a proxy previously cached the old logout endpoint.
    for cookie_name in (
        app.config.get("SESSION_COOKIE_NAME", "session"),
        app.config.get("REMEMBER_COOKIE_NAME", "remember_token"),
        "session",
        "remember_token",
    ):
        response.delete_cookie(cookie_name, path="/", samesite="Lax")
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("admin/dashboard.html")


LIFE_CATEGORIES = {"daily": "日常", "travel": "旅行", "food": "美食"}


@admin_bp.route("/real_life_photos", methods=["GET", "POST"])
@login_required
def real_life_photos():
    photos = data_utils.read_json("real_life_photos.json") or []
    if request.method == "POST":
        category = request.form.get("category", "daily")
        description = request.form.get("description", "").strip()[:160]
        uploaded_files = request.files.getlist("files")
        if category not in LIFE_CATEGORIES:
            category = "daily"
        if not uploaded_files or not any(file.filename for file in uploaded_files):
            flash("请选择至少一张照片。", "danger")
            return redirect(request.url)

        success_count = 0
        errors = []
        for file in uploaded_files:
            if not file.filename:
                continue
            try:
                _, url_path, unique_name = local_storage_utils.save_real_life_photo(file)
                photos.append({
                    "key": unique_name,
                    "url": url_path,
                    "category": category,
                    "description": description,
                    "upload_time": datetime.now().isoformat(timespec="seconds"),
                    "show": True,
                })
                success_count += 1
            except ValueError as error:
                errors.append(f"{file.filename}: {error}")

        data_utils.write_json("real_life_photos.json", photos)
        if success_count:
            flash(f"已发布 {success_count} 张现实相册照片。", "success")
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("admin.real_life_photos"))

    photos.sort(key=lambda photo: photo.get("upload_time", ""), reverse=True)
    for photo in photos:
        photo["thumb_url"] = local_storage_utils.get_thumbnail_url(photo.get("url", ""))
    return render_template(
        "admin/real_life_photos.html",
        photos=photos,
        categories=LIFE_CATEGORIES,
        heif_available=local_storage_utils.HEIF_AVAILABLE,
    )


@admin_bp.route("/real_life_photos/<path:file_key>", methods=["POST"])
@login_required
def update_real_life_photo(file_key):
    photos = data_utils.read_json("real_life_photos.json") or []
    category = request.form.get("category", "daily")
    if category not in LIFE_CATEGORIES:
        category = "daily"
    for photo in photos:
        if photo.get("key") == file_key:
            photo["category"] = category
            photo["description"] = request.form.get("description", "").strip()[:160]
            photo["show"] = "show" in request.form
            data_utils.write_json("real_life_photos.json", photos)
            flash("照片信息已保存。", "success")
            break
    return redirect(url_for("admin.real_life_photos"))


@admin_bp.route("/real_life_photos/<path:file_key>/delete", methods=["POST"])
@login_required
def delete_real_life_photo(file_key):
    photos = data_utils.read_json("real_life_photos.json") or []
    deleted = next((photo for photo in photos if photo.get("key") == file_key), None)
    if deleted:
        local_storage_utils.delete_local_file(deleted.get("url", ""))
        photos = [photo for photo in photos if photo.get("key") != file_key]
        data_utils.write_json("real_life_photos.json", photos)
        flash("照片已删除。", "success")
    return redirect(url_for("admin.real_life_photos"))


# 编辑首页
@admin_bp.route("/edit_home", methods=["GET", "POST"])
@login_required
def edit_home():
    if request.method == "POST":
        print("=" * 50)
        print("收到编辑首页 POST 请求")
        print("表单数据:", request.form)

        current_home = data_utils.read_json("home.json")
        current_accounts = current_home.get("accounts", [])
        accounts = []
        account_count = 1 if app.config["SITE_MODE"] == "single" else 2
        for i in range(1, account_count + 1):
            acc = {
                "id": request.form.get(f"account{i}_id", ""),
                "server": request.form.get(f"account{i}_server", ""),
                "region": request.form.get(f"account{i}_region", ""),
                "avatar": request.form.get(f"account{i}_avatar", ""),
                "standing_image": request.form.get(f"account{i}_standing", ""),
            }
            accounts.append(acc)
        if account_count == 1:
            accounts.extend(current_accounts[1:2])
        bg_images_text = request.form.get("bg_images", "")
        bg_images = [url.strip() for url in bg_images_text.splitlines() if url.strip()]
        home_data = {
            "accounts": accounts,
            "bg_images": bg_images,
            # 如果已经删除了个人形象字段，下面两行也应删除
            # 'profile_image': request.form.get('profile_image', ''),
            "standing_image": request.form.get("standing_image", ""),
        }
        data_utils.write_json("home.json", home_data)
        print("写入后的 home.json:", data_utils.read_json("home.json"))
        flash("首页信息已保存", "success")
        return redirect(url_for("admin.edit_home"))
    home_data = data_utils.read_json("home.json")
    return render_template("admin/edit_home.html", home=home_data)


# 编辑角色铭牌
@admin_bp.route("/edit_characters", methods=["GET", "POST"])
@login_required
def edit_characters():
    if request.method == "POST":
        current_characters = data_utils.read_json("characters.json")
        characters = []
        character_count = 1 if app.config["SITE_MODE"] == "single" else 2
        for i in range(1, character_count + 1):
            char = {
                "name": request.form.get(f"char{i}_name", ""),
                "free_company": request.form.get(f"char{i}_fc", ""),
                "city": request.form.get(f"char{i}_city", ""),
                "start_date": request.form.get(f"char{i}_start_date", ""),
                "badge_image": request.form.get(f"char{i}_badge", ""),  # 图片URL
                "background_image": request.form.get(f"char{i}_background", ""),  # 新增
            }
            characters.append(char)
        if character_count == 1:
            characters.extend(current_characters[1:2])
        data_utils.write_json("characters.json", characters)
        flash("角色信息已保存", "success")
        return redirect(url_for("admin.edit_characters"))
    chars = data_utils.read_json("characters.json")
    return render_template("admin/edit_characters.html", characters=chars)


# 编辑职业等级
@admin_bp.route("/edit_jobs", methods=["GET", "POST"])
@login_required
def edit_jobs():
    if request.method == "POST":
        # 解析所有职业等级，表单字段命名规则：jobs[类别][索引][字段]
        # 由于表单复杂，我们简单采用：为每个职业生成输入框，如 tanks_0_level, tanks_0_icon 等
        jobs_data = {}
        categories = [
            "tanks",
            "healers",
            "melee",
            "ranged_physical",
            "ranged_magic",
            "crafters",
            "gatherers",
        ]
        for cat in categories:
            cat_list = []
            i = 0
            while True:
                level_key = f"{cat}_{i}_level"
                icon_key = f"{cat}_{i}_icon"
                if level_key not in request.form:
                    break
                full_name = request.form.get(f"{cat}_{i}_full_name", "")
                abbr = request.form.get(f"{cat}_{i}_abbr", "")
                level = request.form.get(level_key, "0")
                icon = request.form.get(icon_key, "")
                cat_list.append(
                    {
                        "full_name": full_name,
                        "abbr": abbr,
                        "level": int(level) if level.isdigit() else 0,
                        "icon": icon,
                    }
                )
                i += 1
            jobs_data[cat] = cat_list
        data_utils.write_json("jobs.json", jobs_data)
        flash("职业等级已保存", "success")
        return redirect(url_for("admin.edit_jobs"))
    jobs_data = data_utils.read_json("jobs.json")
    return render_template("admin/edit_jobs.html", jobs=jobs_data)


# 编辑社交链接
@admin_bp.route("/edit_social", methods=["GET", "POST"])
@login_required
def edit_social():
    if request.method == "POST":
        print("=" * 50)
        print("收到编辑社交链接的 POST 请求")
        print("表单数据:", request.form)

        # 注意：这里用花括号 {} 定义字典，而不是方括号 []
        social = {
            "shizhijia": request.form.get("shizhijia", ""),
            "shizhijia_image": request.form.get("shizhijia_image", ""),
            "steam": request.form.get("steam", ""),
            "steam_image": request.form.get("steam_image", ""),
            "oopz": request.form.get("oopz", ""),  # 修正为 oopz
            "oopz_image": request.form.get("oopz_image", ""),  # 修正为 oopz_image
            "qq": request.form.get("qq", ""),
            "qq_image": request.form.get("qq_image", ""),
            "bilibili": request.form.get("bilibili", ""),
            "bilibili_image": request.form.get("bilibili_image", ""),
            "bilibili_live": request.form.get("bilibili_live", ""),
            "bilibili_live_image": request.form.get("bilibili_live_image", ""),
        }

        data_utils.write_json("social.json", social)
        print("写入后的 social.json:", data_utils.read_json("social.json"))

        flash("社交链接已保存", "success")
        return redirect(url_for("admin.edit_social"))

    # GET 请求：读取数据并渲染模板
    social = data_utils.read_json("social.json")
    return render_template("admin/edit_social.html", social=social)


# 编辑导航栏（背景图片、logo）
@admin_bp.route("/edit_navbar", methods=["GET", "POST"])
@login_required
def edit_navbar():
    with open("C:\\inetpub\\wwwroot\\ffxiv_site\\debug_start.txt", "w") as f:
        f.write("edit_navbar 路由被访问了")
    if request.method == "POST":
        print("=" * 50)
        print("收到 POST 请求 - edit_navbar")
        print("表单原始数据:", request.form)

        body_bg_value = request.form.get("body_bg", "【未获取到】")
        navbar_bg_value = request.form.get("navbar_bg", "【未获取到】")
        navbar_logo_value = request.form.get("navbar_logo", "【未获取到】")

        print(f"body_bg: {body_bg_value}")
        print(f"navbar_bg: {navbar_bg_value}")
        print(f"navbar_logo: {navbar_logo_value}")

        site_config = data_utils.read_json("site_config.json")
        site_config["navbar_bg"] = (
            navbar_bg_value if navbar_bg_value != "【未获取到】" else ""
        )
        site_config["navbar_logo"] = (
            navbar_logo_value if navbar_logo_value != "【未获取到】" else ""
        )
        site_config["body_bg"] = (
            body_bg_value if body_bg_value != "【未获取到】" else ""
        )
        data_utils.write_json("site_config.json", site_config)

        print("写入后的 site_config:", data_utils.read_json("site_config.json"))

        flash("导航栏设置已保存", "success")
        return redirect(url_for("admin.edit_navbar"))

    site_config = data_utils.read_json("site_config.json")
    return render_template("admin/edit_navbar.html", site_config=site_config)


# 游戏记录上传管理（使用本地存储）
@admin_bp.route('/gallery_upload', methods=['GET', 'POST'])
@login_required
def gallery_upload():
    if request.method == 'POST':
        # 获取上传的所有文件
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or uploaded_files[0].filename == '':
            flash('未选择文件', 'danger')
            return redirect(request.url)
        
        success_count = 0
        error_count = 0
        gallery_data = data_utils.read_json('gallery.json') or []
        
        for file in uploaded_files:
            if file.filename == '':
                continue
            # 保存到本地 static/uploads/
            _file_path, url_path, unique_name = local_storage_utils.save_uploaded_file(file)
            
            if url_path:
                # 上传到 COS（如果可用）
                
                # 记录文件信息
                gallery_data.append({
                    'key': unique_name,
                    'url': url_path,
                    'url_local': url_path,
                    'upload_time': datetime.now().isoformat(),
                    'show': True
                })
                success_count += 1
            else:
                error_count += 1
        
        # 保存更新后的 gallery.json
        data_utils.write_json('gallery.json', gallery_data)
        
        flash(f'上传完成：成功 {success_count} 个，失败 {error_count} 个', 'success')
        return redirect(url_for('admin.gallery_upload'))
    
    # GET 请求：显示已上传文件列表
    gallery_data = data_utils.read_json('gallery.json') or []
    return render_template('admin/gallery_upload.html', files=gallery_data)


@admin_bp.route("/gallery_delete/<path:file_key>")
@login_required
def gallery_delete(file_key):
    # 从gallery.json查找文件信息
    gallery_data = data_utils.read_json("gallery.json")
    file_item = None
    for item in gallery_data:
        if item["key"] == file_key:
            file_item = item
            break
    
    if file_item:
        # 从本地删除文件
        local_storage_utils.delete_local_file(file_item.get("url_local", file_item["url"]))
        # 从COS删除（如果可用）
        # 从gallery.json移除记录
        gallery_data = [item for item in gallery_data if item["key"] != file_key]
        data_utils.write_json("gallery.json", gallery_data)
        flash("文件已删除", "success")
    else:
        flash("文件不存在", "danger")
    return redirect(url_for("admin.gallery_upload"))
# 显示路由
@admin_bp.route("/gallery_toggle", methods=["POST"])
@login_required
def gallery_toggle():
    data = request.get_json()
    key = data.get("key")
    show = data.get("show")
    gallery_data = data_utils.read_json("gallery.json")
    for item in gallery_data:
        if item["key"] == key:
            item["show"] = show
            break
    data_utils.write_json("gallery.json", gallery_data)
    return jsonify({"success": True})


# 留言管理（回复）
@admin_bp.route("/messages")
@login_required
def messages():
    messages_list = data_utils.read_json("messages.json")
    return render_template("admin/messages.html", messages=messages_list)


@admin_bp.route("/reply_message/<message_id>", methods=["POST"])
@login_required
def reply_message(message_id):
    reply_content = request.form.get("reply")
    if reply_content and validate_emote_content(reply_content):
        messages = data_utils.read_json("messages.json")
        for msg in messages:
            if msg["id"] == message_id:
                msg["replies"].append(
                    {
                        "content": reply_content,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
                break
        data_utils.write_json("messages.json", messages)
        flash("回复已保存", "success")
    elif reply_content:
        flash("每条回复最多使用 10 个有效的情感动作", "danger")
    else:
        flash("回复内容不能为空", "danger")
    return redirect(url_for("admin.messages"))


@admin_bp.route("/edit_intro", methods=["GET", "POST"])
@login_required
def edit_intro():
    if request.method == "POST":
        intro = {"content": request.form.get("content", "")}
        data_utils.write_json("intro.json", intro)
        flash("个人介绍已保存", "success")
        return redirect(url_for("admin.edit_intro"))
    intro = data_utils.read_json("intro.json")
    return render_template("admin/edit_intro.html", intro=intro)



@admin_bp.route("/edit_music", methods=["GET", "POST"])
@login_required
def edit_music():
    if request.method == "POST":
        config = {
            "defaultSource": request.form.get("defaultSource", "local"),
            "sources": [
                {
                    "id": "local",
                    "name": "本地",
                    "icon": "fa-solid fa-music",
                    "playlist": []
                },
                {
                    "id": "netease",
                    "name": "网易云",
                    "icon": "fa-brands fa-napster",
                    "embedType": request.form.get("netease_type", "playlist"),
                    "embedId": request.form.get("netease_id", ""),
                    "autoPlay": "netease_auto" in request.form
                },
                {
                    "id": "qqmusic",
                    "name": "QQ音乐",
                    "icon": "fa-brands fa-qq",
                    "embedType": request.form.get("qq_type", "song"),
                    "embedId": request.form.get("qq_id", ""),
                    "autoPlay": "qq_auto" in request.form
                }
            ]
        }
        data_utils.write_json("music.json", config)
        flash("音乐设置已保存", "success")
        return redirect(url_for("admin.edit_music"))

    config = data_utils.read_json("music.json")
    netease = next((s for s in config.get("sources", []) if s["id"] == "netease"), {"embedType":"playlist","embedId":"","autoPlay":False})
    qqmusic = next((s for s in config.get("sources", []) if s["id"] == "qqmusic"), {"embedType":"song","embedId":"","autoPlay":False})
    return render_template("admin/edit_music.html", config=config, netease=netease, qqmusic=qqmusic)
@admin_bp.route('/gallery_edit/<path:file_key>', methods=['GET', 'POST'])
@login_required
def gallery_edit(file_key):
    gallery_data = data_utils.read_json('gallery.json')
    file_item = None
    for item in gallery_data:
        if item['key'] == file_key:
            file_item = item
            break
    if not file_item:
        flash('文件不存在', 'danger')
        return redirect(url_for('admin.gallery_upload'))
    
    if request.method == 'POST':
        file_item['account'] = request.form.get('account', '1')
        file_item['description'] = request.form.get('description', '')
        file_item['sticky'] = 'sticky' in request.form
        data_utils.write_json('gallery.json', gallery_data)
        flash('文件信息已更新', 'success')
        return redirect(url_for('admin.gallery_upload'))
    
    return render_template('admin/gallery_edit.html', file=file_item)

@admin_bp.route('/delete_message/<message_id>')
@login_required
def delete_message(message_id):
    messages = data_utils.read_json('messages.json')
    # 查找并删除指定 ID 的留言
    new_messages = [msg for msg in messages if msg.get('id') != message_id]
    if len(new_messages) == len(messages):
        flash('留言不存在', 'danger')
    else:
        data_utils.write_json('messages.json', new_messages)
        flash('留言已删除', 'success')
    return redirect(url_for('admin.messages'))


# ---------- 缩略图服务 ----------
@app.route("/thumbnails/<path:filename>")
def serve_thumbnail(filename):
    """提供缩略图服务，自动生成并缓存"""
    result = local_storage_utils.serve_thumbnail(filename)
    if result:
        result.headers['Cache-Control'] = 'public, max-age=604800, immutable'
        return result
    # 回退: 尝试返回原图
    upload_folder = local_storage_utils.get_upload_folder()
    file_path = os.path.join(upload_folder, filename.replace('_thumb', ''))
    if os.path.exists(file_path):
        return send_file(file_path)
    return ("", 404)


# 注册蓝图
app.register_blueprint(admin_bp, url_prefix="/admin")



# 添加上下文处理器，让所有模板自动获取 site_config
@app.context_processor
def inject_site_config():
    site_config = data_utils.read_json("site_config.json")
    return dict(
        site_config=site_config,
        thumbnail_url=local_storage_utils.get_thumbnail_url,
        intro_video_url=app.config.get("INTRO_VIDEO_URL", ""),
        site_mode=app.config["SITE_MODE"],
        visible_character_count=1 if app.config["SITE_MODE"] == "single" else 2,
    )



# ---------- 音乐播放器 API ----------
@app.route("/api/music/config")
def music_config():
    config = data_utils.read_json("music.json")
    for src in config.get("sources", []):
        if src.get("id") == "local":
            base_url = "/static/music/"
            for item in src.get("playlist", []):
                if item.get("file") and not item["file"].startswith("http"):
                    item["file"] = base_url + item["file"]
    return jsonify(config)

@app.route("/ping")
def ping():
    with open("C:\\inetpub\\wwwroot\\ffxiv_site\\ping_debug.txt", "w") as f:
        f.write("ping 路由被访问")
    return "pong"

@app.after_request
def set_response_headers(response):
    # 对图片/CSS/JS设置浏览器缓存
    if response.mimetype and response.mimetype.startswith('image/'):
        # Local uploads use unique hash filenames, so they can be cached safely for a year.
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    elif response.mimetype and response.mimetype.startswith('video/'):
        # Uploaded media use content-addressed names and support range requests.
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    elif response.mimetype in ('text/css', 'application/javascript', 'application/x-javascript'):
        # versioned_static appends a content version, so long browser caching is safe.
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    elif response.mimetype and response.mimetype.startswith('font/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    # 只对HTML页面强制UTF-8，不干扰图片等静态资源
    if response.mimetype == 'text/html':
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        # Authentication-aware pages must never reuse HTML rendered before
        # login/logout. Static assets remain long-lived above.
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


# ---------- 启动 ----------
if __name__ == "__main__":
    # 生产环境建议使用waitress等，但开发调试可以用内置服务器
    app.run(host="0.0.0.0", port=5000, debug=True)  # debug模式仅用于开发，生产应关闭
