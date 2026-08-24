# Render 部署指南

## 最推荐：GitHub + Render Blueprint

1. 新建一个 GitHub 仓库，例如 `xhs-screenshot-tool`。
2. 上传本目录里的所有文件，注意不要上传 `runs/`、`__pycache__/`。
3. 登录 Render，点击 `New`，选择 `Blueprint`。
4. 连接 GitHub 仓库。
5. Render 会读取 `render.yaml` 并创建 Docker Web Service。
6. 部署完成后，打开 Render 分配的线上地址。

## 手动创建 Render Web Service

如果不用 Blueprint：

1. Render 点击 `New`，选择 `Web Service`。
2. 连接 GitHub 仓库。
3. Runtime 选择 `Docker`。
4. Instance 建议选择 `Starter` 或更高。
5. 添加 Persistent Disk：
   - Mount Path: `/app/runs`
   - Size: `5GB`
6. 保存并部署。

## 环境变量

Dockerfile 已内置默认值，通常不用手动填：

- `HOST=0.0.0.0`
- `PORT=8788`
- `CHROME_PATH=/usr/bin/chromium`
- `NODE_PATH=/usr/bin/node`

## 重要限制

- 这是浏览器自动化服务，不适合静态托管。
- 免费实例会休眠，第一次打开和第一次截图会慢。
- 小红书如果返回登录、验证码、异常访问，工具会标记失败，不会绕过。
