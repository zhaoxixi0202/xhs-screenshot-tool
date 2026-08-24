# 小红书笔记截图工具

本工具支持本机运行，也支持用 Docker 部署到 Render 这类云平台。

- 单条链接截图，输出 PNG。
- Excel 批量截图，读取表格里的笔记链接列，把截图写回指定输出列。

它不会登录账号、不会保存登录态、不会处理验证码，也不会绕过平台限制。遇到登录墙、验证码、异常访问或连续失败，会自动退避并中止，失败行会保留现场截图供人工判断。

## 启动

```sh
/Users/zhaoxixi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 xhs_screenshot_tool/app.py
```

打开：

```text
http://127.0.0.1:8788
```

## Excel 批量

1. 上传 `.xlsx` 文件。
2. 填工作表名、链接列、输出列，例如 `Sheet1`、`A`、`B`。
3. 点击开始批量截图。
4. 完成后下载写回图片的新表格。

输出列如果处在合并单元格内，会写入合并区域左上角。工具还会在输出列右侧写入状态、原因和图片路径，方便断点续跑和人工复核。

## 运行要求

- 本机需安装 Google Chrome。
- 当前实现默认截取浏览器当前可见页面，不做整页长截图。
- 建议一次 100 行以内或分批运行；默认会自动限速，遇到疑似风控会拉长等待时间。

## Render 部署

推荐用 GitHub 连接 Render：

1. 把 `xhs_screenshot_tool` 目录作为一个仓库推到 GitHub。
2. 在 Render 新建 `Blueprint` 或 `Web Service`。
3. 选择这个仓库。
4. 如果用 Blueprint，Render 会读取 `render.yaml`。
5. 如果手动建 Web Service，选择 Docker 环境，根目录填仓库根目录，端口使用默认 `8788`。
6. 部署成功后打开 Render 给出的 `https://...onrender.com` 地址。

线上注意事项：

- 免费/低配实例冷启动会慢，首次截图会更慢。
- 批量截图会占用服务器 CPU 和内存，建议 Render 至少用 starter 级别实例。
- 上传的 Excel、截图和结果表保存在 `/app/runs`，`render.yaml` 已配置 5GB 磁盘。
- 本工具不登录、不保存账号、不处理验证码；遇到登录墙/风控会标失败并留现场截图。
