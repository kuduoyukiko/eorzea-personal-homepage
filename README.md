# Eorzea Personal Homepage

一个以艾欧泽亚冒险档案为主题的个人主页模板。项目使用 Flask、Jinja 和原生 JavaScript 构建，包含双角色首页、职业等级、相册分类、现实生活记录、留言簿、音乐播放器与后台管理。

> 本项目是玩家制作的非官方个人项目，与 Square Enix 无隶属或合作关系。公开仓库不包含游戏素材、作者私人图片、视频、音乐、访客留言或生产环境密钥。

## 功能

- 双角色冒险档案首页；
- 首次访问视频序章与“重温序章”；
- 角色信息和职业等级管理；
- 按角色分类的艾欧泽亚相册；
- 现实生活照片与社交链接；
- 支持回复和表情的留言簿；
- 本地、网易云和 QQ 音乐配置；
- Flask-Login 后台管理；
- 图片缩略图、懒加载、Range 视频播放和静态资源缓存；
- Windows + Waitress 部署脚本。

## 技术栈

- Python 3.10+
- Flask / Flask-Login
- Pillow / pillow-heif
- Waitress
- Bootstrap 与 Font Awesome（本地依赖）
- JSON 文件存储，无需数据库

## 快速开始

### 1. 获取代码

```bash
git clone https://github.com/kuduoyukiko/eorzea-personal-homepage.git
cd eorzea-personal-homepage
```

### 2. 创建虚拟环境

Windows PowerShell：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Linux/macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. 配置环境变量

复制示例文件：

```powershell
Copy-Item .env.example .env
```

Linux/macOS：

```bash
cp .env.example .env
```

修改 `.env`：

```dotenv
SECRET_KEY=请替换为足够长的随机字符串
ADMIN_USERNAME=admin
ADMIN_PASSWORD=请替换为强密码
INTRO_VIDEO_URL=/static/uploads/your-intro-video.mp4
SITE_MODE=dual
```

### 单角色与双角色模式

网站默认使用双角色版。修改 `.env` 后重启应用即可切换：

```dotenv
SITE_MODE=single  # 单角色：仅展示和编辑角色 1
SITE_MODE=dual    # 双角色：展示和编辑两个角色
```

单角色模式会使用角色 1 的资料并采用居中首页构图，同时隐藏双人记忆内容。角色 2 的已有数据不会被删除；切回 `dual` 后会恢复显示。

### 新留言邮件通知（QQ 邮箱）

在 QQ 邮箱网页版开启 SMTP 服务并生成授权码，然后在 `.env` 中填写：

```dotenv
MAIL_SMTP_HOST=smtp.qq.com
MAIL_SMTP_PORT=465
MAIL_TIMEOUT=10
MAIL_SENDER=你的发件QQ邮箱@qq.com
MAIL_AUTH_CODE=你的QQ邮箱SMTP授权码
MAIL_RECIPIENT=接收通知的邮箱@example.com
SITE_URL=http://你的域名
```

`MAIL_AUTH_CODE` 是 QQ 邮箱生成的 SMTP 授权码，不是 QQ 密码。请勿把 `.env` 提交到 Git。只有访客成功提交新留言时才会通知；邮件发送失败不会影响留言保存，错误会记录在服务器日志中。

可以使用下面的命令生成 `SECRET_KEY`：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

不要提交 `.env`。生产环境使用 HTTP 时，登录 Cookie 无法获得 HTTPS 的传输保护；公开部署建议配置 HTTPS，并将 `SESSION_COOKIE_SECURE` 与 `REMEMBER_COOKIE_SECURE` 调整为 `True`。

### 4. 启动

开发环境：

```bash
python app.py
```

访问：

- 前台：`http://127.0.0.1:5000/`
- 后台：`http://127.0.0.1:5000/admin/login`

生产环境推荐：

```bash
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

Windows 用户也可以参考 [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md) 和 `scripts/` 下的启动、停止与计划任务脚本。

## 添加素材

本仓库有意不附带 FFXIV 游戏素材和作者个人媒体。详细边界与目录约定请阅读 [ASSETS.md](ASSETS.md)。

常用目录：

```text
static/
├─ images/          # 主题装饰与自有图片
├─ music/           # 已获授权的音乐
└─ uploads/         # 后台上传内容与序章视频
```

将 MP4 放进 `static/uploads/` 后，在 `.env` 中设置 `INTRO_VIDEO_URL`。建议使用 H.264 + AAC、`yuv420p` 和 fast-start MP4，以获得更好的浏览器兼容性。

## 数据文件

运行时数据位于 `data/`，包括：

- `home.json`
- `characters.json`
- `jobs.json`
- `gallery.json`
- `real_life_photos.json`
- `messages.json`
- `social.json`
- `intro.json`
- `music.json`
- `site_config.json`

这些文件包含私人内容，因此默认被 `.gitignore` 排除。首次运行缺少文件时，应用会使用空数据或默认结构；也可以先登录后台逐项填写。

迁移或备份时，请单独备份 `data/`、`static/uploads/` 和 `.env`。不要把生产数据提交到公开仓库。

## 后台与安全

- 后台账号从 `.env` 读取；
- 登录默认只在当前浏览器会话有效；
- 注销会清理新旧认证 Cookie；
- 含认证状态的 HTML 使用 `no-store`，避免注销后显示旧编辑入口；
- 图片、视频、CSS、JavaScript 和字体使用长期缓存；
- 上传大小上限当前为 200MB。

公开部署前建议再增加：HTTPS、反向代理限速、登录失败限制、CSRF 保护和定期离线备份。

## 腾讯云 CDN参考

当前项目可使用 HTTP 源站 5000 端口：

- 源站类型：自有源；
- 回源协议：HTTP；
- 源站地址：服务器公网 IP；
- 回源端口：5000；
- 回源 Host：你的正式域名；
- `/static`：可长期缓存；
- HTML 与 `/admin`：不要缓存；
- 视频需要支持 Range 请求。

不同 CDN控制台规则会变化，请以当前腾讯云文档为准。

## 项目结构

```text
app.py                 # 路由、后台与响应缓存策略
config.py              # 环境变量配置
templates/             # Jinja 页面模板
static/css/            # 页面样式
static/js/             # 交互与播放器
static/vendor/         # 本地前端依赖
utils/data_utils.py    # JSON 数据读写
utils/local_storage_utils.py  # 上传与缩略图
scripts/               # Windows 部署脚本
```

## 开源与版权

程序代码采用 [MIT License](LICENSE)。这不代表 FINAL FANTASY XIV 的名称、角色、图标、美术、音乐或其他游戏内容采用 MIT License。使用自己的素材时，你也需要确认相应授权。

欢迎提交 Issue 或 Pull Request 改进代码。请勿在 Issue 中粘贴 `.env`、后台密码、访客数据或服务器信息。
