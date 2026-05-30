# 部署指南

把这套系统部署到自己服务器的步骤。假设你已经有：

- 一台 Linux 服务器（Ubuntu 22.04+ 推荐，2 核 4G 起步够 5-10 人）
- 一个域名 + DNS 控制权（A 记录指到服务器 IP）
- 服务器 80 + 443 端口能从公网访问
- 一个 DeepSeek API key（或其他 OpenAI 兼容服务商的 key）

预计时间：**首次 30-60 分钟**，熟练后 10 分钟。

---

## 1. 服务器准备

### 安装 Docker + Docker Compose

```bash
sudo apt update && sudo apt install -y curl python3-cryptography
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# 重新登录让 docker group 生效
```

### 配置 docker 加速器（仅大陆服务器）

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run"
  ]
}
EOF
sudo systemctl restart docker
```

---

## 2. 拉代码

```bash
sudo mkdir -p /opt/team-ai-workspace
sudo chown $USER:$USER /opt/team-ai-workspace
cd /opt
git clone https://github.com/ruoyouxifengsi/team-ai-workspace.git
cd team-ai-workspace
```

如果 GitHub 在你的网络下访问慢，用镜像或开代理。

---

## 3. 配置环境变量

```bash
cp .env.example .env
nano .env
```

必填项：

```bash
# 你的域名（要先把 DNS A 记录指到这台服务器的 IP）
DOMAIN=ai.example.com

# admin 账号
ADMIN_USERNAME=admin
ADMIN_INITIAL_PASSWORD=<改成一个强密码>

# DeepSeek（或其他 OpenAI 兼容 API）
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Fernet 对称加密密钥（用户个人 key 用这个加密存）
# 生成：python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=<贴上面命令的输出>

# CORS 允许的来源（通常就你的域名）
CORS_ORIGINS=https://ai.example.com

# 其他
SESSION_TTL_HOURS=168
```

**关键提醒**：

- `FERNET_KEY` 设定后**永远不能改**，改了所有用户存的个人 API key 都解不开
- 立刻把 `.env` 备份到密码管理器
- `.env` 在 `.gitignore` 里，不会被提交到 git

---

## 4. 起容器

```bash
sudo docker compose up -d --build
```

首次 build 会下载基础镜像（python:3.11-slim、node:20-alpine、nginx:1.27-alpine、caddy:2-alpine）+ 装依赖，大约 5-10 分钟。

等完了看下：

```bash
sudo docker compose ps
```

应该看到 4 个容器都是 `Up`：backend / frontend / caddy / backup。

```bash
sudo docker compose logs --tail=30 backend
```

应该看到 `Uvicorn running on http://0.0.0.0:8000`，没 traceback。

---

## 5. 验证

```bash
curl -s http://localhost/api/healthz
```

返回 `{"status":"ok"}` 说明 backend 起来了。

```bash
curl -s https://你的域名/api/healthz
```

可能要等 Caddy 自动申请 Let's Encrypt 证书（30-90 秒），然后能返回 `{"status":"ok"}`。

浏览器打开 `https://你的域名/`，应该看到登录页。用 admin 账号密码登录 → 应该进入空白的 workspace 三栏布局。

---

## 6. 创建队员账号

admin 登录 → 顶部「用户管理」→ 「新建用户」→ 填写用户名和初始密码 → 发给队员。

队员第一次登录后可以在「设置」里改密码（未来版本）。当前版本队员改密码要 admin 在后台改。

---

## 7. 部署后建议

### 备份

`backup` 容器已经每天定时把 sqlite 数据库 + 上传的文件打 tar 包到 `./data/backups/`。建议加一个 cron 任务把 `./data/backups/` 同步到对象存储（阿里 OSS / 腾讯 COS）：

```bash
# 安装 ossutil 或 coscli 后
0 4 * * * /usr/local/bin/ossutil cp -r /opt/team-ai-workspace/data/backups/ oss://your-bucket/team-ai-workspace/ >> /var/log/oss-sync.log 2>&1
```

### 监控

最简陋的方案：

```bash
# /etc/cron.d/team-ai-monitor
*/5 * * * * root curl -fsS https://你的域名/api/healthz > /dev/null || echo "team-ai-workspace down at $(date)" | mail -s "ALERT" you@example.com
```

进阶：上 uptime kuma / better stack 等。

### 升级

主仓有新功能时：

```bash
cd /opt/team-ai-workspace
git pull
sudo docker compose build backend frontend
sudo docker compose up -d backend frontend
```

数据库 schema 升级是 backend 启动时自动跑 `migrate.upgrade_schema()`，无需手动操作。

---

## 8. 故障排查

### 浏览器打不开（中国大陆部署）

如果你的域名是大陆云服务器 IP 而**没有 ICP 备案**，运营商可能在 443 端口拦截：

- 症状：ping 通、curl 内部测试通，浏览器 ERR_CONNECTION_RESET（或类似）
- 临时方案：改用非标端口。修改 `Caddyfile`：

```caddyfile
http://{$DOMAIN} {
    redir https://{$DOMAIN}:8443{uri} permanent
}

{$DOMAIN}:8443 {
    encode zstd gzip
    handle_path /api/* {
        rewrite * /api{path}
        reverse_proxy backend:8000
    }
    handle /api/* {
        reverse_proxy backend:8000
    }
    handle {
        reverse_proxy frontend:80
    }
}
```

`docker-compose.yml` 里 caddy 的 ports 改成 `"8443:8443"`（保留 `"80:80"` 给 ACME 续期用）。

服务器防火墙开 8443 入站。重启 caddy：`sudo docker compose up -d caddy`。

URL 变成 `https://你的域名:8443/`，能用。备案完成后改回 443。

### pip install 在大陆服务器 timeout

修改 `backend/Dockerfile`：

```Dockerfile
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e .
```

重新 build：`sudo docker compose build --no-cache backend`。

### 部分容器重启后 502

```
caddy-1 | dial tcp: lookup backend on 127.0.0.11:53: server misbehaving
```

整体 down + up 一次：

```bash
sudo docker compose down && sudo docker compose up -d
```

### Let's Encrypt 申请失败

- 检查域名 A 记录是否正确指向服务器
- 80 端口是否对外开放（ACME HTTP-01 challenge 必须从公网访问 80）
- 看 caddy 日志：`sudo docker compose logs caddy | grep -i acme`

### 后端启动报 `FERNET_KEY` 缺失

- 检查 `.env` 里 `FERNET_KEY` 是否填了
- 检查 `docker-compose.yml` 里 `backend.environment` 是否包含 `FERNET_KEY: ${FERNET_KEY}`
- 重启 backend：`sudo docker compose up -d backend`

---

## 9. 卸载

```bash
cd /opt/team-ai-workspace
sudo docker compose down -v  # -v 同时清 volume，会丢数据！
sudo rm -rf /opt/team-ai-workspace
```

---

## 安全 checklist（生产环境）

- [ ] `.env` 备份到密码管理器
- [ ] `ADMIN_INITIAL_PASSWORD` 改成强密码
- [ ] SSH 改密钥登录，禁用密码
- [ ] 服务器防火墙只开必要端口（22 + 80 + 443 或 8443）
- [ ] 数据库备份同步到云存储
- [ ] 监控脚本就位
- [ ] DNS 域名锁

至此部署完成。如果遇到本文档没覆盖的问题，欢迎在 GitHub issue 反馈。
