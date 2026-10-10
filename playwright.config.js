// @ts-check
const { defineConfig } = require('@playwright/test');

const BASE_URL = process.env.PLN_E2E_BASE_URL || 'http://127.0.0.1:18000';

module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 60000,
  expect: { timeout: 15000 },
  use: {
    baseURL: BASE_URL,
    headless: true,
    viewport: { width: 1280, height: 720 },
    reducedMotion: 'reduce',
    actionTimeout: 10000,
    navigationTimeout: 15000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        launchOptions: { args: ['--no-sandbox'] },
      },
    },
  ],
  reporter: [
    ['list'],
    // Write the generated report to a gitignored path. The previous target
    // (evidence/rc026-r2/playwright/playwright-report.json) is tracked in git,
    // so any local run silently overwrote committed audit evidence. Curated,
    // SHA-bound evidence summaries belong in evidence/ instead.
    ['json', { outputFile: 'playwright-report/playwright-report.json' }],
  ],
  // Release verification runs must be visible, not headless:
  //   npx playwright test --headed
  // The headless default is kept so the suite still runs on machines without a
  // display; a headed run is required for release evidence.
  // No video evidence in repo — Phase I policy
});
