#!/usr/bin/env node
/**
 * CoAgent 15s 精简 Demo — 前 3s Hero 抓注意力，完整链路压缩展示
 * 用法: bash scripts/record_demo_15s.sh
 */
import { chromium } from 'playwright';
import { mkdirSync, renameSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const ROOT = process.env.COAGENT_ROOT || join(dirname(fileURLToPath(import.meta.url)), '..');
const BASE = process.env.BASE_URL || 'http://localhost:8000';
const OUT_DIR = join(ROOT, 'docs', 'demos');
const TS = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const TARGET_SEC = Number(process.env.DEMO_TARGET_SEC || 15);
const SCENARIO_TIMEOUT = Number(process.env.DEMO_SCENARIO_TIMEOUT_MS || 180000);

mkdirSync(OUT_DIR, { recursive: true });
mkdirSync(join(OUT_DIR, '.playwright-videos'), { recursive: true });

async function pause(page, ms) {
  await page.waitForTimeout(ms);
}

async function ensureCompletedTrace() {
  const trigger = await fetch(`${BASE}/admin/trigger/s1`, { method: 'POST' });
  if (!trigger.ok) throw new Error(`trigger failed: ${trigger.status}`);
  const { trace_id: traceId } = await trigger.json();
  const deadline = Date.now() + SCENARIO_TIMEOUT;
  while (Date.now() < deadline) {
    const res = await fetch(`${BASE}/admin/incidents/${traceId}`);
    if (res.ok) {
      const inc = await res.json();
      if (inc.status === 'completed' && inc.score_json?.total) return traceId;
    }
    await new Promise((r) => setTimeout(r, 400));
  }
  return traceId;
}

console.log('=== CoAgent 15s Demo Recorder ===');
console.log('Base URL:', BASE);

try {
  execSync(`curl -sf ${BASE}/health`, { stdio: 'pipe' });
} catch {
  console.error('✗ 请先启动服务: uvicorn app.main:app --port 8000');
  process.exit(1);
}

console.log('→ 预触发 S1，确保处置页可即时展示…');
const traceId = await ensureCompletedTrace();
console.log('→ trace:', traceId);

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  recordVideo: { dir: join(OUT_DIR, '.playwright-videos'), size: { width: 1920, height: 1080 } },
  locale: 'zh-CN',
});
const page = await context.newPage();

try {
  // ── 0–3s 钩子：全屏 Hero + 价值主张 ──
  console.log('→ [0-3s] Hero 钩子');
  await page.goto(`${BASE}/?tab=1`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.pal-hero-title', { timeout: 10000 });
  await pause(page, 3000);

  // ── 3–8s 处置：把握度评分 + 一键重试 ──
  console.log('→ [3-8s] 处置工作台');
  await page.goto(`${BASE}/?tab=2&trace=${encodeURIComponent(traceId)}`, {
    waitUntil: 'domcontentloaded',
  });
  await page.waitForSelector('.decision-score-header', { timeout: SCENARIO_TIMEOUT });
  await pause(page, 1500);
  const retryBtn = page.locator('button:has-text("一键重试")');
  if (await retryBtn.count()) {
    await retryBtn.click();
    await page.waitForSelector('.retry-exec-panel', { timeout: 5000 }).catch(() => {});
    await pause(page, 2200);
  } else {
    await pause(page, 2800);
  }

  // ── 8–12s 因果链 / 知识图谱 ──
  console.log('→ [8-12s] 执行链 & 图谱');
  const chain = page.locator('#execution-chain');
  if (await chain.isVisible()) {
    await chain.scrollIntoViewIfNeeded();
  } else {
    await page.locator('#advanced-panels').scrollIntoViewIfNeeded().catch(() => {});
  }
  await pause(page, 2200);
  await page.locator('.kg-card').first().scrollIntoViewIfNeeded().catch(() => {});
  await pause(page, 2000);

  // ── 12–15s 飞轮收尾 ──
  console.log('→ [12-15s] 审计飞轮');
  await page.goto(`${BASE}/?tab=3`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.flywheel-loop-card', { timeout: 10000 });
  await pause(page, 2800);

  console.log('✓ 录制流程完成');
} catch (err) {
  console.error('✗ 录制失败:', err.message);
  process.exitCode = 1;
} finally {
  const video = page.video();
  await page.close();
  await context.close();
  await browser.close();

  if (video) {
    const rawPath = await video.path();
    const webmPath = join(OUT_DIR, `coagent-demo-15s-${TS}.webm`);
    const mp4Path = join(OUT_DIR, `coagent-demo-15s-${TS}.mp4`);
    if (existsSync(rawPath)) {
      renameSync(rawPath, webmPath);
      console.log('📹 WebM:', webmPath);
      try {
        execSync(
          `ffmpeg -y -i "${webmPath}" -t ${TARGET_SEC} -c:v libx264 -pix_fmt yuv420p -movflags +faststart "${mp4Path}"`,
          { stdio: 'pipe' }
        );
        const dur = execSync(
          `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${mp4Path}"`,
          { encoding: 'utf8' }
        ).trim();
        console.log('🎬 MP4:', mp4Path, `(~${parseFloat(dur).toFixed(1)}s)`);
      } catch {
        console.log('ℹ ffmpeg 转码跳过');
      }
    }
  }
}
