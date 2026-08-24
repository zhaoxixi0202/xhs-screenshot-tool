#!/usr/bin/env node
import fs from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  process.env.GOOGLE_CHROME_BIN,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  path.join(process.env.LOCALAPPDATA || "", "Google\\Chrome\\Application\\chrome.exe"),
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  "/usr/bin/google-chrome",
  "/usr/bin/google-chrome-stable",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].filter(Boolean);

function usage() {
  console.log("Usage: node cdp_screenshot.mjs --job job.json --out result.json");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function writeStatus(job, patch) {
  if (!job.statusPath) return;
  const payload = {
    time: new Date().toISOString(),
    ...patch,
  };
  await fs.writeFile(job.statusPath, JSON.stringify(payload, null, 2)).catch(() => {});
}

async function cancelRequested(job) {
  if (!job.cancelPath) return false;
  try {
    await fs.access(job.cancelPath);
    return true;
  } catch {
    return false;
  }
}

function httpJson(url, method = "GET") {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method }, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        try {
          resolve(JSON.parse(body));
        } catch (err) {
          reject(new Error(`Bad JSON from Chrome: ${err.message}`));
        }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

async function resolveChrome() {
  for (const candidate of CHROME_CANDIDATES) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {}
  }
  throw new Error("Cannot find Chrome. Set CHROME_PATH or install Google Chrome/Chromium.");
}

function defaultChromeUserDataDir() {
  if (process.env.CHROME_USER_DATA_DIR) return process.env.CHROME_USER_DATA_DIR;
  if (process.platform === "darwin") return path.join(os.homedir(), "Library/Application Support/Google/Chrome");
  if (process.platform === "win32") return path.join(process.env.LOCALAPPDATA || "", "Google/Chrome/User Data");
  return path.join(os.homedir(), ".config/google-chrome");
}

class Cdp {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.nextId = 1;
    this.pending = new Map();
  }

  async open() {
    this.ws = new WebSocket(this.wsUrl);
    this.ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(msg.error.message || JSON.stringify(msg.error)));
        else resolve(msg.result || {});
      }
    });
    await new Promise((resolve, reject) => {
      this.ws.addEventListener("open", resolve, { once: true });
      this.ws.addEventListener("error", reject, { once: true });
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error(`CDP timeout: ${method}`));
        }
      }, 30000);
    });
  }

  close() {
    if (this.ws) this.ws.close();
  }
}

async function launchChrome(port, viewport, job = {}) {
  const chromePath = await resolveChrome();
  const useSystemProfile = job.useSystemChromeProfile !== false;
  let profile = useSystemProfile ? defaultChromeUserDataDir() : await fs.mkdtemp(path.join(os.tmpdir(), "xhs-shot-"));
  const headless = process.env.HEADLESS !== "false";
  const args = [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profile}`,
    "--profile-directory=Default",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-session-crashed-bubble",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-features=Translate,AutomationControlled",
    `--window-size=${viewport.width},${viewport.height}`,
    "about:blank",
  ];
  if (headless && !useSystemProfile) args.unshift("--headless=new");
  const child = spawn(chromePath, args, { stdio: "ignore" });
  for (let i = 0; i < 80; i++) {
    try {
      await httpJson(`http://127.0.0.1:${port}/json/version`);
      return { child, profile };
    } catch {
      await sleep(250);
    }
  }
  child.kill();
  if (useSystemProfile) {
    throw new Error("复用本机 Chrome 环境失败。请先完全退出 Chrome 后重试；或取消勾选“复用本机 Chrome 环境”改用临时环境。");
  }
  throw new Error("Chrome did not start. Please check Google Chrome is installed.");
}

async function newPage(port) {
  let target;
  try {
    target = await httpJson(`http://127.0.0.1:${port}/json/new`, "PUT");
  } catch {
    const pages = await httpJson(`http://127.0.0.1:${port}/json`);
    target = pages.find((p) => p.type === "page") || pages[0];
  }
  if (!target?.webSocketDebuggerUrl) throw new Error("Cannot open Chrome page.");
  const cdp = new Cdp(target.webSocketDebuggerUrl);
  await cdp.open();
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Network.enable");
  return cdp;
}

async function evalPage(cdp, expression) {
  const res = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (res.exceptionDetails) throw new Error("Page evaluation failed");
  return res.result?.value;
}

const CLEAN_SCRIPT = String.raw`(() => {
  const textRe = /(手机登录|验证码|手机号|立即登录|扫码登录|登录后推荐更懂你的笔记|安全验证|异常访问)/;
  let removed = 0;
  for (const el of Array.from(document.querySelectorAll('div,section,aside,dialog'))) {
    const st = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    const covers = (st.position === 'fixed' || st.position === 'sticky') &&
      rect.width > innerWidth * 0.35 && rect.height > innerHeight * 0.2;
    const z = Number(st.zIndex) || 0;
    const txt = (el.innerText || '').slice(0, 260);
    const looksLikeNote = /(关注|评论|收藏|分享|赞|展开|收起)/.test(txt) && Array.from(el.querySelectorAll('img,video,canvas')).some((media) => {
      const r = media.getBoundingClientRect();
      return r.width > 160 && r.height > 160;
    });
    if ((covers || z > 1000 || el.tagName === 'DIALOG') && textRe.test(txt) && !looksLikeNote) {
      el.remove();
      removed += 1;
    }
  }
  for (const btn of Array.from(document.querySelectorAll('button,[role=button],.close,.close-btn'))) {
    const txt = (btn.innerText || btn.getAttribute('aria-label') || btn.className || '').toString();
    const r = btn.getBoundingClientRect();
    const parentText = (btn.closest('div,section,aside,dialog')?.innerText || '').slice(0, 260);
    if (/关闭|close|取消|稍后|×|x/i.test(txt) && textRe.test(parentText)) {
      try { btn.click(); removed += 1; } catch {}
    }
  }
  document.documentElement.style.overflow = 'auto';
  document.body.style.overflow = 'auto';
  return removed;
})()`;

const STATUS_SCRIPT = String.raw`(() => {
  const text = (document.body?.innerText || '').replace(/\s+/g, ' ').slice(0, 4000);
  const visible = (el) => {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && st.visibility !== 'hidden' && st.display !== 'none';
  };
  const visibleMedia = Array.from(document.querySelectorAll('img,video,canvas')).filter((el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (r.width < 120 || r.height < 120 || st.visibility === 'hidden' || st.display === 'none') return false;
    if (el.tagName === 'IMG') return el.complete && el.naturalWidth > 80 && el.naturalHeight > 80;
    return true;
  });
  const loginDialog = Array.from(document.querySelectorAll('div,section,aside,dialog')).find((el) => {
    if (!visible(el)) return false;
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    const t = (el.innerText || '').slice(0, 320);
    const covers = (st.position === 'fixed' || st.position === 'sticky' || Number(st.zIndex) > 1000) &&
      r.width > innerWidth * 0.3 && r.height > innerHeight * 0.25;
    return covers && /(手机登录|验证码|手机号|扫码登录|登录后推荐更懂你的笔记|立即登录)/.test(t);
  });
  const blocked = /(安全验证|验证码|访问异常|操作频繁|请求频繁|滑块|登录后查看|请登录|当前环境存在异常|IP at risk|secure network|300012)/i.test(text) && !loginDialog;
  const loading = /(加载中|正在加载|loading)/i.test(text);
  const noteCandidates = Array.from(document.querySelectorAll([
    '[class*="note-detail"]',
    '[class*="note-container"]',
    '[class*="detail-container"]',
    '[class*="engage-bar"]',
    '[class*="interaction"]',
    'main',
    'section',
    'div'
  ].join(','))).filter((el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (st.visibility === 'hidden' || st.display === 'none') return false;
    if (r.width < 620 || r.height < 420) return false;
    const t = (el.innerText || '').replace(/\s+/g, ' ').slice(0, 1200);
    const hasNoteActions = /(关注|评论|收藏|分享|点赞|赞)/.test(t);
    const hasNoteText = /#[^ ]+|评论|关注|发布|展开|收起/.test(t) || t.length > 180;
    const mediaInside = Array.from(el.querySelectorAll('img,video,canvas')).some((media) => visibleMedia.includes(media));
    const centered = r.left > -20 && r.right < innerWidth + 20 && r.top > -20 && r.bottom < innerHeight + 40;
    return centered && mediaInside && hasNoteActions && hasNoteText;
  });
  const onExploreHome = /xiaohongshu\.com\/(explore\/?)?($|[?#])/.test(location.href) && !noteCandidates.length;
  const hasNoteDetail = noteCandidates.length > 0 && !loginDialog;
  return {
    blocked,
    loading,
    media: visibleMedia.length,
    hasNoteDetail,
    hasLoginDialog: Boolean(loginDialog),
    onExploreHome,
    title: document.title,
    url: location.href,
    textSample: text.slice(0, 180)
  };
})()`;

async function waitForReady(cdp, timeoutMs) {
  const start = Date.now();
  let last = null;
  while (Date.now() - start < timeoutMs) {
    await evalPage(cdp, CLEAN_SCRIPT).catch(() => 0);
    last = await evalPage(cdp, STATUS_SCRIPT).catch((err) => ({ error: err.message }));
    if (last?.blocked) return { ok: false, blocked: true, reason: `疑似验证/风控：${last.textSample || ""}` };
    if (last?.hasNoteDetail && !last?.loading) {
      await sleep(900);
      await evalPage(cdp, CLEAN_SCRIPT).catch(() => 0);
      const confirm = await evalPage(cdp, STATUS_SCRIPT).catch(() => last);
      if (confirm?.hasNoteDetail && !confirm?.hasLoginDialog) return { ok: true, blocked: false, reason: "" };
    }
    await sleep(700);
  }
  if (last?.hasLoginDialog) {
    return { ok: false, blocked: false, reason: "登录弹窗未能关闭，已保留现场截图" };
  }
  if (last?.onExploreHome) {
    return { ok: false, blocked: false, reason: "只打开到小红书首页/Explore 瀑布流，未进入笔记详情页，已保留现场截图" };
  }
  return { ok: false, blocked: false, reason: `未识别到笔记详情页：${last?.textSample || last?.error || "无可见内容"}` };
}

async function capture(cdp, file) {
  const res = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  });
  await fs.writeFile(file, Buffer.from(res.data, "base64"));
}

async function shootOne(cdp, item, job, attempt) {
  await writeStatus(job, { stage: "row", message: `正在处理第 ${item.row} 行，第 ${attempt} 次尝试`, row: item.row, attempt });
  const name = `row_${String(item.row || item.index).padStart(4, "0")}_${attempt}`;
  const successFile = path.join(job.outputDir, `${name}.png`);
  const failFile = path.join(job.outputDir, `${name}_failure.png`);
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: job.viewport.width,
    height: job.viewport.height,
    deviceScaleFactor: job.viewport.deviceScaleFactor || 1,
    mobile: false,
  });
  await cdp.send("Page.navigate", { url: item.url });
  await sleep(1200);
  const ready = await waitForReady(cdp, job.timeoutMs);
  if (!ready.ok) {
    await capture(cdp, failFile).catch(() => {});
    return { ...item, status: "失败", reason: ready.reason, failureScreenshot: failFile, blocked: ready.blocked };
  }
  await capture(cdp, successFile);
  return { ...item, status: "成功", reason: "", screenshot: successFile, blocked: false };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--help") || !args.length) return usage();
  const jobPath = args[args.indexOf("--job") + 1];
  const outPath = args[args.indexOf("--out") + 1];
  if (!jobPath || !outPath) throw new Error("Missing --job or --out");
  const job = JSON.parse(await fs.readFile(jobPath, "utf8"));
  await fs.mkdir(job.outputDir, { recursive: true });
  const port = 9222 + Math.floor(Math.random() * 1000);
  await writeStatus(job, { stage: "chrome", message: "正在启动 Chrome 截图环境" });
  const chrome = await launchChrome(port, job.viewport, job);
  const results = [];
  let delay = job.delayMs || 3500;
  let consecutive = 0;
  try {
    await writeStatus(job, { stage: "browser", message: "Chrome 已启动，正在打开截图页面" });
    const cdp = await newPage(port);
    for (const item of job.items) {
      if (await cancelRequested(job)) {
        await fs.writeFile(outPath, JSON.stringify({ results, stopped: true, reason: "用户手动终止截图任务" }, null, 2));
        await writeStatus(job, { stage: "cancelled", message: "用户手动终止截图任务" });
        break;
      }
      let result = null;
      for (let attempt = 1; attempt <= (job.maxRetries || 1); attempt++) {
        result = await shootOne(cdp, item, job, attempt).catch(async (err) => {
          const failFile = path.join(job.outputDir, `row_${String(item.row || item.index).padStart(4, "0")}_${attempt}_crash.png`);
          await capture(cdp, failFile).catch(() => {});
          return { ...item, status: "失败", reason: err.message, failureScreenshot: failFile, blocked: false };
        });
        if (result.status === "成功") break;
        await sleep(delay * attempt);
      }
      results.push(result);
      await writeStatus(job, { stage: "done-row", message: `第 ${item.row} 行处理完成：${result.status}`, row: item.row });
      if (result.status === "成功") {
        consecutive = 0;
        delay = Math.max(job.minDelayMs || 3000, Math.round(delay * 0.92));
      } else {
        consecutive += 1;
        if (result.blocked) delay = Math.min(job.maxDelayMs || 60000, Math.round(delay * 2.2));
      }
      await fs.writeFile(outPath, JSON.stringify({ results, stopped: false }, null, 2));
      if (consecutive >= (job.maxConsecutiveFailures || 5)) {
        await fs.writeFile(outPath, JSON.stringify({ results, stopped: true, reason: "连续失败/被拦达到阈值，已中止" }, null, 2));
        await writeStatus(job, { stage: "stopped", message: "连续失败/被拦达到阈值，已中止" });
        break;
      }
      await sleep(delay + Math.floor(Math.random() * 1200));
    }
    await writeStatus(job, { stage: "complete", message: "截图完成，正在写回 Excel" });
    cdp.close();
  } finally {
    chrome.child.kill();
  }
}

main().catch(async (err) => {
  console.error(err.stack || err.message);
  process.exit(1);
});
