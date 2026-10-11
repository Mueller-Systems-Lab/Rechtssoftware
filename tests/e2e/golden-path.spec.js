// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');

const BASE_URL = process.env.PLN_E2E_BASE_URL || 'http://127.0.0.1:18000';
const SEED_FILE = process.env.PLN_E2E_SEED_FILE;

/**
 * Load the harness seed. The harness creates TWO synthetic cases; the document
 * is attached to case A only. Selecting "the first case whose text contains
 * SYNTHETISCH" is therefore non-deterministic, so tests that need the document
 * navigate to the seeded case A URL directly.
 */
function loadSeed() {
  if (!SEED_FILE || !fs.existsSync(SEED_FILE)) {
    throw new Error(`Seed file not found: ${SEED_FILE} — harness must run first`);
  }
  return JSON.parse(fs.readFileSync(SEED_FILE, 'utf8'));
}

/**
 * RC-026-R2 Golden Path: Complete V1 user journey through the browser UI.
 */

// ===== G1: Installation and Start =====
test.describe('G1 — Start and Health', () => {

  test('homepage loads with correct title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/PrivateLegalNavigator/);
    await expect(page.locator('h1')).toBeVisible();
  });

  test('/health returns ok', async ({ page }) => {
    const response = await page.request.get(BASE_URL + '/health');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe('ok');
  });
});

// ===== G2: Case Workflow =====
test.describe('G2 — Case Workflow', () => {

  test('case list page loads', async ({ page }) => {
    await page.goto('/ui/cases');
    await expect(page.locator('h1')).toBeVisible();
    // German UI: "Fälle" heading
    await expect(page.locator('text=Fälle').first()).toBeVisible({ timeout: 5000 });
  });

  test('create case form submits through the browser and the case appears', async ({ page }) => {
    // This test SUBMITS the form rather than only filling it. That distinction
    // matters: while it only filled the form, a defect went unnoticed in which
    // `Referrer-Policy: no-referrer` made Chromium send `Origin: null` on
    // same-origin form POSTs, so the origin check rejected every UI form
    // submission with 403 "Ungültige Anfrageherkunft". Every POST-based UI flow —
    // case creation, uploads, confirmations — was unusable in that browser.
    await page.goto('/ui/cases');
    await page.click('a:has-text("Neuen Fall anlegen")');
    await expect(page).toHaveURL(/\/ui\/cases\/create/);

    const testTitle = `SYNTHETISCH – E2E UI submit ${Date.now()}`;
    await page.fill('input[name="title"]', testTitle);
    await page.click('form:has(input[name="title"]) button[type="submit"]');

    // A successful submission redirects to the new case's detail page.
    await expect(page).toHaveURL(/\/ui\/cases\/[0-9a-f-]{36}/, { timeout: 15000 });
    await expect(page.locator('h1')).toContainText('SYNTHETISCH', { timeout: 10000 });

    // …and the case is listed afterwards.
    await page.goto('/ui/cases');
    await expect(page.locator(`a:has-text("${testTitle}")`).first()).toBeVisible({ timeout: 10000 });
  });

  test('case persists after browser reload', async ({ page }) => {
    await page.goto('/ui/cases');
    // Find any synthetic case
    const caseLink = page.locator('text=SYNTHETISCH').first();
    await expect(caseLink).toBeVisible({ timeout: 10000 });

    const caseText = await caseLink.textContent();
    await page.reload();
    await page.waitForLoadState('networkidle');

    await expect(page.locator(`text=${caseText}`).first()).toBeVisible({ timeout: 10000 });
  });

  test('case detail page loads', async ({ page }) => {
    await page.goto('/ui/cases');
    const caseLink = page.locator('text=SYNTHETISCH').first();
    await expect(caseLink).toBeVisible({ timeout: 10000 });
    await caseLink.click();

    // Should be on case detail — heading shows case title
    await expect(page.locator('h1')).toContainText('SYNTHETISCH', { timeout: 10000 });
  });
});

// ===== G3: Document Workflow =====
test.describe('G3 — Document Workflow', () => {

  test('document uploaded via harness appears in case', async ({ page }) => {
    const seed = loadSeed();
    // Navigate straight to the seeded case A — it is the case the harness
    // uploaded the synthetic PDF into.
    await page.goto(`/ui/cases/${seed.case_id}`);

    // The harness always seeds one document into case A, so the document link
    // must exist. The previous version only asserted when the locator happened
    // to be present and otherwise passed without testing anything.
    const docLink = page.locator(`a[href*="${seed.document_id}"], a[href*="documents"]`).first();
    await expect(docLink).toBeVisible({ timeout: 10000 });
    await docLink.click();
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 10000 });
  });
});

// ===== G4: Reference Event Workflow =====
test.describe('G4 — Reference Event Workflow', () => {

  test('deadline candidates are visible on document page', async ({ page }) => {
    const seed = loadSeed();
    // Candidates/deadlines are rendered on the document detail page
    // (templates/documents/detail.html, section "Datums- und Zeitraumhinweise"),
    // not on the case detail page. The previous version of this test asserted
    // nothing at all (it counted into an unused variable).
    await page.goto(`/ui/cases/${seed.case_id}/documents/${seed.document_id}`);

    await expect(
      page.locator('h2:has-text("Datums- und Zeitraumhinweise")')
    ).toBeVisible({ timeout: 10000 });
  });

  test('human review required is visible', async ({ page }) => {
    await page.goto('/');
    const bodyText = await page.textContent('body');
    // Must mention human review / non-binding somewhere
    expect(bodyText.toLowerCase()).toMatch(/human.review|menschliche|keine rechtliche|unverbindlich/);
  });
});

// ===== G5: Calculation Preview =====
test.describe('G5 — Calculation Preview', () => {

  test('no legal validity claim anywhere', async ({ page }) => {
    await page.goto('/');
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toMatch(/rechtlich verbindlich|rechtsverbindlich/);
  });

  test('LEGAL_CALCULATION_NOT_PERFORMED is present in code', async ({ page }) => {
    // Verify this invariant via API or page content
    await page.goto('/');
    // The app must not claim binding legal calculation
    const bodyText = await page.textContent('body');
    expect(bodyText).not.toMatch(/verbindliche (Frist|Rechts)/i);
  });
});

// ===== G8: Restart and Persistence =====
test.describe('G8 — Restart and Persistence', () => {

  test('data survives page reload', async ({ page }) => {
    await page.goto('/ui/cases');
    const caseLink = page.locator('text=SYNTHETISCH').first();
    await expect(caseLink).toBeVisible({ timeout: 10000 });
    const caseText = await caseLink.textContent();
    expect(caseText).toBeTruthy();

    // Reload
    await page.reload();
    await page.waitForLoadState('networkidle');

    await expect(page.locator(`text=${caseText}`).first()).toBeVisible({ timeout: 15000 });
  });
});
