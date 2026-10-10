// @ts-check
const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.PLN_E2E_BASE_URL || 'http://127.0.0.1:18000';

/**
 * RC-026-R2 G6: Legal Source Search
 * G7: Timeline and Evidence Pack
 */

// ===== G6: Legal Source Search =====
test.describe('G6 — Legal Source Search', () => {

  test('legal sources page loads', async ({ page }) => {
    await page.goto('/ui/legal-sources');
    // Page should load with legal sources section
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
  });

  test('legal source search input exists', async ({ page }) => {
    // The dedicated search page (/ui/legal-sources/search) always renders the
    // search form (templates/m7a/legal_sources_search.html), so this is asserted
    // unconditionally. The previous version silently passed when the locator was
    // absent and therefore proved nothing.
    await page.goto('/ui/legal-sources/search');
    const searchInput = page.locator('input[type="search"], input[name="q"]');
    await expect(searchInput.first()).toBeVisible({ timeout: 10000 });
  });

  test('no external requests to non-GII hosts', async ({ page }) => {
    const externalRequests = [];
    page.on('request', (request) => {
      const url = request.url();
      // Only allow localhost and GII
      if (!url.startsWith(BASE_URL) && !url.includes('gesetze-im-internet.de') && !url.startsWith('data:')) {
        externalRequests.push(url);
      }
    });

    await page.goto('/');
    await page.goto('/ui/legal-sources');

    // No unexpected external requests
    expect(externalRequests.filter(u => !u.includes('127.0.0.1') && !u.includes('localhost'))).toHaveLength(0);
  });
});

// ===== G7: Timeline and Evidence Pack =====
test.describe('G7 — Timeline and Evidence Pack', () => {

  test('timeline page accessible from case', async ({ page }) => {
    await page.goto('/ui/cases');
    const caseLink = page.locator('a:has-text("Playwright E2E Testfall")').first();
    // The harness seeds this case; its absence is a real failure, not a reason
    // to silently pass.
    await expect(caseLink).toBeVisible({ timeout: 10000 });
    await caseLink.click();

    // Case detail always links to the legal timeline
    // (templates/cases/detail.html → url_for('case_legal_timeline')).
    const timelineLink = page.locator('a[href*="legal-timeline"], a[href*="timeline"]').first();
    await expect(timelineLink).toBeVisible({ timeout: 10000 });
    await timelineLink.click();
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
  });

  test('evidence pack accessible', async ({ page }) => {
    await page.goto('/ui/cases');
    const caseLink = page.locator('a:has-text("Playwright E2E Testfall")').first();
    await expect(caseLink).toBeVisible({ timeout: 10000 });
    await caseLink.click();

    // Case detail always links to the evidence pack
    // (templates/cases/detail.html → url_for('evidence_pack')).
    const evidenceLink = page.locator('a[href*="evidence-pack"]').first();
    await expect(evidenceLink).toBeVisible({ timeout: 10000 });
    await evidenceLink.click();
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
  });
});
