# Windows Server 2012 自动部署

目标环境：

- 网站目录：`C:\inetpub\wwwroot\ffxiv_site`
- Python：`C:\python\python.exe`
- 分支：`main`
- 运行端口：`5000`
- 部署方式：Windows 任务计划程序每分钟检查 GitHub

## 受保护的服务器数据

以下内容不会进入 Git，也不会被自动部署覆盖：

- `.env`
- `data/*.json`
- `static/uploads/`
- `.deploy/` 中的密钥、PID 和日志

## 首次连接服务器

1. 在 GitHub 创建名为 `ffxiv_site` 的 Private 仓库，并把本地 `main` 分支推送上去。
2. 在服务器安装 Git for Windows，并确保 `git`、`ssh` 和 `ssh-keygen` 可在 PowerShell 中运行。
3. 在服务器创建只读部署密钥：

```powershell
cd C:\inetpub\wwwroot\ffxiv_site
New-Item -ItemType Directory -Path .deploy -Force
ssh-keygen -t ed25519 -C "ffxiv-site-deploy" -f .deploy\github_deploy_key -N '""'
Get-Content .deploy\github_deploy_key.pub
```

4. 把显示的公钥添加到 GitHub 仓库的 `Settings > Deploy keys > Add deploy key`，不要勾选写入权限。
5. 在服务器 PowerShell 中设置 Git 使用该密钥，其中 `<YOUR_GITHUB_USER>` 替换为 GitHub 用户名：

```powershell
$env:GIT_SSH_COMMAND='ssh -i C:\inetpub\wwwroot\ffxiv_site\.deploy\github_deploy_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new'
git remote add origin git@github.com:<YOUR_GITHUB_USER>/ffxiv_site.git
git fetch origin main
git branch --set-upstream-to=origin/main main
git config core.sshCommand "ssh -i C:/inetpub/wwwroot/ffxiv_site/.deploy/github_deploy_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
```

6. 以管理员身份安装自动部署和开机启动任务：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\inetpub\wwwroot\ffxiv_site\scripts\install_windows_tasks.ps1
```

## 日常更新

本地完成修改后：

```powershell
git add .
git commit -m "更新网站"
git push
```

服务器会在一分钟内拉取更新并重启网站。部署日志位于：

```text
C:\inetpub\wwwroot\ffxiv_site\.deploy\deploy.log
```
