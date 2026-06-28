#!/usr/bin/env node
/**
 * CoAgent 运维控制台浏览器录制脚本
 * 用法: bash scripts/record_demo.sh
 * 产出: docs/demos/coagent-demo-<timestamp>.webm (+ .mp4)
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
const SLOW = Number(process.env.DEMO_SLOW_MS || 800);
const SCENARIO_TIMEOUT = Number(process.env.DEMO_SCENARIO_TIMEOUT_MS || 300000);
const VIEWPORT = { width: 1920, height: 1080 };

mkdirSync(OUT_DIR, { recursive: true });
mkdirSync(join(OUT_DIR, '.playwright-videos'), { recursive: true });

async function pause(page, ms = SLOW) {
  await page.waitForTimeout(ms);
}

async function waitForCompletedIncident(traceId) {
  const deadline = Date.now() + SCENARIO_TIMEOUT;
  while (Date.now() < deadline) {
    const res = await fetch(`${BASE}/admin/incidents/${traceId}`);
    if (res.ok) {
      const inc = await res.json();
      if (inc.status === 'completed' && inc.score_json?.total != null) return inc;
      if (inc.status === 'failed') {
        throw new Error(`场景 ${traceId} 流水线失败，请使用 MOCK_LLM=true 录制`);
      }
    }
    await new Promise((r) => setTimeout(r, 400));
  }
  throw new Error(`等待决策结果超时: ${traceId}`);
}

async function runDemoScenario(page, scenarioId) {
  const beforeRes = await fetch(`${BASE}/admin/incidents`);
  const beforeIds = beforeRes.ok
    ? new Set((await beforeRes.json()).map((i) => i.trace_id))
    : new Set();

  await page.locator(`[data-demo-scenario="${scenarioId}"]`).click();

  let traceId = null;
  const deadline = Date.now() + SCENARIO_TIMEOUT;
  while (Date.now() < deadline) {
    const res = await fetch(`${BASE}/admin/incidents`);
    if (res.ok) {
      const items = await res.json();
      const fresh = items.filter((i) => i.scenario_id === scenarioId && !beforeIds.has(i.trace_id));
      if (fresh.length) {
        traceId = fresh[0].trace_id;
        break;
      }
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  if (!traceId) throw new Error(`未获取 trace_id: ${scenarioId}`);

  await waitForCompletedIncident(traceId);
  await page.goto(`${BASE}/?tab=2&trace=${encodeURIComponent(traceId)}`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.decision-score-header', { timeout: 30000 });
  return traceId;
}

async function scrollTo(page, selector) {
  const el = page.locator(selector).first();
  if (await el.count()) {
    await el.scrollIntoViewIfNeeded();
    await pause(page, 600);
  }
}

console.log('=== CoAgent Demo Recorder ===');
console.log('Base URL:', BASE);

try {
  execSync(`curl -sf ${BASE}/health`, { stdio: 'pipe' });
} catch {
  console.error('✗ 请先启动服务: MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --port 8000');
  process.exit(1);
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: VIEWPORT,
  recordVideo: { dir: join(OUT_DIR, '.playwright-videos'), size: VIEWPORT },
  locale: 'zh-CN',
});
const page = await context.newPage();

try {
  // ── 1. 事故总览 ──
  console.log('→ 事故总览');
  await page.goto(`${BASE}/?tab=1`, { waitUntil: 'networkidle' });
  await pause(page, 2000);
  await scrollTo(page, '.pitch-narrative');
  await pause(page, 2500);
  await scrollTo(page, '.demo-script');
  await pause(page, 2000);

  // ── 2. 处置工作台 · S1 ──
  console.log('→ 处置工作台 · S1');
  await page.goto(`${BASE}/?tab=2`, { waitUntil: 'networkidle' });
  await pause(page, 1500);
  await runDemoScenario(page, 's1');
  await pause(page, 2000);
  await scrollTo(page, '#execution-chain');
  await pause(page, 2500);
  await scrollTo(page, '#decision-panel');
  await pause(page, 2000);

  // 一键重试（S1 🟢）
  const retryBtn = page.locator('button:has-text("一键重试")');
  if (await retryBtn.count()) {
    await retryBtn.click();
    await pause(page, 1500);
  }

  // ── 3. S2 空检索 · 🟡 ──
  console.log('→ S2 空检索');
  await runDemoScenario(page, 's2');
  await pause(page, 2000);
  await scrollTo(page, '#decision-panel');
  await pause(page, 2500);

  // ── 4. S3 超预算 · 🔴 ──
  console.log('→ S3 超预算');
  await runDemoScenario(page, 's3');
  await pause(page, 2000);
  await scrollTo(page, '#execution-chain');
  await pause(page, 2000);
  await scrollTo(page, '#advanced-panels');
  await pause(page, 2000);

  // 审计复盘 · 飞轮
  console.log('→ 审计复盘');
  await page.goto(`${BASE}/?tab=3`, { waitUntil: 'networkidle' });
  await pause(page, 1500);
  await scrollTo(page, '.flywheel-loop-card');
  await pause(page, 1500);

  const auditRow = page.locator('.audit-row-link').first();
  if (await auditRow.count()) {
    await auditRow.click();
    await page.waitForURL(/trace=/, { timeout: 15000 });
    await page.waitForSelector('#audit-detail-panel', { timeout: 15000 });
    await scrollTo(page, '#audit-detail-panel');
    await pause(page, 1000);
    const feedbackUp = page.locator('#btn-feedback-up');
    if (await feedbackUp.count() && !(await feedbackUp.isDisabled())) {
      await feedbackUp.click();
      await pause(page, 2000);
    }
  }

  await scrollTo(page, '#audit-log-list');
  await pause(page, 2000);

  // 回到总览收尾
  await page.goto(`${BASE}/?tab=1`, { waitUntil: 'networkidle' });
  await scrollTo(page, '.pal-hero-title');
  await pause(page, 3000);

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
    const webmPath = join(OUT_DIR, `coagent-demo-${TS}.webm`);
    if (existsSync(rawPath)) {
      renameSync(rawPath, webmPath);
      console.log('📹 WebM:', webmPath);

      try {
        const mp4Path = join(OUT_DIR, `coagent-demo-${TS}.mp4`);
        execSync(
          `ffmpeg -y -i "${webmPath}" -c:v libx264 -pix_fmt yuv420p -movflags +faststart "${mp4Path}"`,
          { stdio: 'pipe' }
        );
        console.log('🎬 MP4: ', mp4Path);
      } catch {
        console.log('ℹ ffmpeg 转码跳过，可直接使用 WebM');
      }
    }
  }
}
