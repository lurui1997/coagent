#!/usr/bin/env node
/**
 * 导出架构 HTML 为 PNG / 技术架构动图 GIF
 * 用法: bash scripts/export_diagrams.sh
 */
import { chromium } from 'playwright';
import { mkdirSync, renameSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { execSync } from 'child_process';

const ROOT = process.env.COAGENT_ROOT || join(dirname(fileURLToPath(import.meta.url)), '..');
const DIAGRAM_DIR = join(ROOT, 'docs', 'diagrams');
const HTML = join(DIAGRAM_DIR, 'coagent-architecture.html');
const URL = pathToFileURL(HTML).href;
const VIEWPORT = { width: 1440, height: 900 };

const OUT = {
  arch: join(DIAGRAM_DIR, 'coagent-architecture.png'),
  flow: join(DIAGRAM_DIR, 'coagent-business-flow.png'),
  pipelineGif: join(DIAGRAM_DIR, 'coagent-pipeline.gif'),
};

mkdirSync(join(DIAGRAM_DIR, '.playwright-videos'), { recursive: true });

console.log('=== CoAgent Diagram Export ===');
console.log('Source:', HTML);

const browser = await chromium.launch({ headless: true });

try {
  // ── 技术架构 PNG ──
  {
    const ctx = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    await page.goto(URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1800);
    await page.locator('#view-arch').screenshot({ path: OUT.arch, fullPage: true });
    await ctx.close();
    console.log('📐 Arch PNG:', OUT.arch);
  }

  // ── 业务流程 PNG ──
  {
    const ctx = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    await page.goto(URL, { waitUntil: 'networkidle' });
    await page.click('[data-view="flow"]');
    await page.waitForTimeout(600);
    await page.locator('#view-flow').screenshot({ path: OUT.flow });
    await ctx.close();
    console.log('📋 Flow PNG:', OUT.flow);
  }

  // ── 技术架构动图 GIF（流水线条带 + 完整 #view-arch，含动画循环） ──
  {
    const EXPORT_WIDTH = 1440;
    const GIF_FPS = 6;
    const PIPELINE_STEP_MS = 1200;
    const PIPELINE_STEPS = 6;
    const LOOP_CYCLES = 1;
    const RECORD_MS = Math.round(PIPELINE_STEP_MS * PIPELINE_STEPS * LOOP_CYCLES);

    const prepPage = await browser.newPage();
    await prepPage.setViewportSize({ width: EXPORT_WIDTH, height: 900 });
    await prepPage.goto(URL, { waitUntil: 'networkidle' });
    await prepPage.waitForTimeout(1200);

    const captureHeight = await prepPage.evaluate(() => {
      document.querySelector('header')?.style.setProperty('display', 'none');
      document.querySelector('.wrap')?.style.setProperty('padding', '0 1.5rem 1rem');
      document.body.style.overflow = 'hidden';

      document.querySelectorAll('.canvas').forEach((c) => c.classList.remove('active'));
      document.getElementById('view-arch').classList.add('active');

      const strip = document.getElementById('pipelineStrip');
      const arch = document.getElementById('view-arch');
      if (!strip || !arch) throw new Error('Missing #pipelineStrip or #view-arch');

      strip.scrollIntoView({ block: 'start' });
      const stripBox = strip.getBoundingClientRect();
      const archBox = arch.getBoundingClientRect();
      return Math.ceil(archBox.bottom - stripBox.top + 12);
    });

    await prepPage.close();

    const videoDir = join(DIAGRAM_DIR, '.playwright-videos');
    for (const f of (await import('fs')).readdirSync(videoDir)) {
      if (f.endsWith('.webm')) (await import('fs')).unlinkSync(join(videoDir, f));
    }
    const ctx = await browser.newContext({
      viewport: { width: EXPORT_WIDTH, height: captureHeight },
      recordVideo: { dir: videoDir, size: { width: EXPORT_WIDTH, height: captureHeight } },
    });
    const page = await ctx.newPage();
    await page.goto(URL, { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      document.querySelector('header')?.style.setProperty('display', 'none');
      document.querySelector('.wrap')?.style.setProperty('padding', '0 1.5rem 1rem');
      document.body.style.overflow = 'hidden';

      document.querySelectorAll('.canvas').forEach((c) => c.classList.remove('active'));
      document.getElementById('view-arch').classList.add('active');

      document.getElementById('pipelineStrip')?.scrollIntoView({ block: 'start' });
    });
    await page.waitForTimeout(1500);
    await page.waitForTimeout(RECORD_MS);
    await ctx.close();

    const raw = (await import('fs')).readdirSync(videoDir).find((f) => f.endsWith('.webm'));
    if (!raw) throw new Error('No architecture video captured');
    const webm = join(videoDir, raw);
    execSync(
      `ffmpeg -y -i "${webm}" -t ${(RECORD_MS / 1000 + 0.3).toFixed(2)} -vf "fps=${GIF_FPS},scale=1200:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" -loop 0 "${OUT.pipelineGif}"`,
      { stdio: 'inherit' },
    );
    console.log('🔄 Architecture GIF:', OUT.pipelineGif, `(${EXPORT_WIDTH}×${captureHeight} → 1200px wide, ${GIF_FPS}fps, ${RECORD_MS}ms)`);
  }
} finally {
  await browser.close();
}

console.log('✓ Done');
