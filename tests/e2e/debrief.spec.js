// @ts-check
const { test, expect } = require('@playwright/test');

const CALDERA_URL = process.env.CALDERA_URL || 'http://localhost:8888';
const PLUGIN_ROUTE = '/#/plugins/debrief';

// ---------------------------------------------------------------------------
// Helper: navigate to the debrief plugin page inside magma
// ---------------------------------------------------------------------------
async function navigateToDebrief(page) {
  await page.goto(`${CALDERA_URL}${PLUGIN_ROUTE}`, { waitUntil: 'networkidle' });
}

// Fake operations payload for mocking
const MOCK_OPERATIONS = [
  { id: 'op-001', name: 'Test Operation Alpha', state: 'finished', planner: { name: 'atomic' }, objective: { name: 'default' }, start: '2025-01-01 00:00:00' },
  { id: 'op-002', name: 'Test Operation Beta', state: 'running', planner: { name: 'batch' }, objective: { name: 'custom-obj' }, start: '2025-01-02 12:00:00' },
];

const MOCK_REPORT = {
  operations: [
    {
      name: 'Test Operation Alpha',
      state: 'finished',
      planner: { name: 'atomic' },
      objective: { name: 'default' },
      start: '2025-01-01 00:00:00',
      host_group: [
        { paw: 'abc123', host: 'workstation1', platform: 'windows', username: 'admin', privilege: 'Elevated', exe_name: 'sandcat.exe' },
      ],
      chain: [
        { id: 'link-1', status: 0, finish: '2025-01-01 00:01:00', ability: { name: 'whoami' }, paw: 'abc123', command: 'd2hvYW1p' },
      ],
    },
  ],
  ttps: {},
};

const MOCK_SECTIONS = {
  report_sections: [
    { key: 'main-summary', name: 'Main Summary' },
    { key: 'statistics', name: 'Statistics' },
    { key: 'agents', name: 'Agents' },
    { key: 'attackpath-graph', name: 'Attack Path Graph' },
    { key: 'steps-graph', name: 'Steps Graph' },
    { key: 'tactic-graph', name: 'Tactic Graph' },
    { key: 'technique-graph', name: 'Technique Graph' },
    { key: 'fact-graph', name: 'Fact Graph' },
    { key: 'tactic-technique-table', name: 'Tactic/Technique Table' },
    { key: 'steps-table', name: 'Steps Table' },
    { key: 'facts-table', name: 'Facts Table' },
  ],
};

// ===========================================================================
// 1. Plugin page loads
// ===========================================================================
test.describe('Debrief plugin page load', () => {
  test('should display the Debrief heading', async ({ page }) => {
    await navigateToDebrief(page);
    const heading = page.locator('h2', { hasText: 'Debrief' });
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });

  test('should display campaign analytics description', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(
      page.locator('text=Campaign Analytics')
    ).toBeVisible({ timeout: 15_000 });
  });

  test('should render Graph Settings button', async ({ page }) => {
    await navigateToDebrief(page);
    const btn = page.locator('button', { hasText: 'Graph Settings' });
    await expect(btn).toBeVisible({ timeout: 15_000 });
  });

  test('should render Download PDF Report button', async ({ page }) => {
    await navigateToDebrief(page);
    const btn = page.locator('button', { hasText: 'Download PDF Report' });
    await expect(btn).toBeVisible({ timeout: 15_000 });
  });

  test('should render Download Operation JSON button', async ({ page }) => {
    await navigateToDebrief(page);
    const btn = page.locator('button', { hasText: 'Download Operation JSON' });
    await expect(btn).toBeVisible({ timeout: 15_000 });
  });

  test('should have an operation select dropdown', async ({ page }) => {
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await expect(select).toBeVisible({ timeout: 15_000 });
  });

  test('should have a horizontal rule separator', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('hr').first()).toBeVisible({ timeout: 15_000 });
  });
});

// ===========================================================================
// 2. Operation selection for debrief
// ===========================================================================
test.describe('Debrief operation selection', () => {
  test('should fetch operations from the API', async ({ page }) => {
    const response = await page.request.get(`${CALDERA_URL}/api/v2/operations`);
    expect(response.ok()).toBeTruthy();
    const ops = await response.json();
    expect(Array.isArray(ops)).toBeTruthy();
  });

  test('buttons should be disabled when no operation is selected', async ({ page }) => {
    await navigateToDebrief(page);
    const pdfBtn = page.locator('button', { hasText: 'Download PDF Report' });
    await expect(pdfBtn).toBeDisabled({ timeout: 15_000 });
    const jsonBtn = page.locator('button', { hasText: 'Download Operation JSON' });
    await expect(jsonBtn).toBeDisabled();
    const settingsBtn = page.locator('button', { hasText: 'Graph Settings' });
    await expect(settingsBtn).toBeDisabled();
  });

  test('operations dropdown should populate from API', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await navigateToDebrief(page);
    const options = page.locator('select option');
    // Should have at least the mock operations plus the default disabled option
    await expect(options).toHaveCount(3, { timeout: 15_000 }); // 1 disabled + 2 ops
  });

  test('selecting an operation should trigger report loading', async ({ page }) => {
    let reportRequested = false;
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) => {
      reportRequested = true;
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      });
    });
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(2000);
    expect(reportRequested).toBeTruthy();
  });
});

// ===========================================================================
// 3. Report section display (tabs: stats, agents, steps, tactics, facts)
// ===========================================================================
test.describe('Debrief report section display', () => {
  test('should show tabs when an operation is selected (mocked)', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);

    // Tab labels should be visible
    await expect(page.locator('a', { hasText: 'Stats' })).toBeVisible();
    await expect(page.locator('a', { hasText: 'Agents' })).toBeVisible();
    await expect(page.locator('a', { hasText: 'Steps' })).toBeVisible();
    await expect(page.locator('a', { hasText: 'Tactics & Techniques' })).toBeVisible();
    await expect(page.locator('a', { hasText: 'Fact Graph' })).toBeVisible();
  });

  test('Stats tab should show operation statistics table headers', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);

    await expect(page.locator('th', { hasText: 'Name' }).first()).toBeVisible();
    await expect(page.locator('th', { hasText: 'State' }).first()).toBeVisible();
    await expect(page.locator('th', { hasText: 'Planner' }).first()).toBeVisible();
    await expect(page.locator('th', { hasText: 'Objective' }).first()).toBeVisible();
    await expect(page.locator('th', { hasText: 'Time' }).first()).toBeVisible();
  });
});

// ===========================================================================
// 4. PDF download button
// ===========================================================================
test.describe('Debrief PDF download', () => {
  test('PDF button should be disabled without operation selection', async ({ page }) => {
    await navigateToDebrief(page);
    const btn = page.locator('button', { hasText: 'Download PDF Report' });
    await expect(btn).toBeDisabled({ timeout: 15_000 });
  });

  test('clicking PDF button should open report modal', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);

    const pdfBtn = page.locator('button', { hasText: 'Download PDF Report' });
    await pdfBtn.click();
    await expect(page.locator('.modal.is-active')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('text=Download Report as PDF')).toBeVisible();
  });

  test('report modal should have Report Sections heading', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);

    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await expect(page.locator('h5', { hasText: 'Report Sections' })).toBeVisible({ timeout: 5_000 });
  });

  test('report modal should show custom logo checkbox', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);

    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await expect(page.locator('text=Use custom logo')).toBeVisible({ timeout: 5_000 });
  });

  test('report modal Download button triggers PDF API call', async ({ page }) => {
    let pdfRequested = false;
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await page.route('**/plugin/debrief/pdf', (route) => {
      pdfRequested = true;
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ filename: 'debrief-report.pdf', pdf_bytes: '' }),
      });
    });
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);

    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await page.waitForTimeout(500);
    // Click the Download button inside the modal
    const downloadBtn = page.locator('.modal.is-active button', { hasText: 'Download' });
    await downloadBtn.click();
    await page.waitForTimeout(2000);
    expect(pdfRequested).toBeTruthy();
  });
});

// ===========================================================================
// 5. JSON export
// ===========================================================================
test.describe('Debrief JSON export', () => {
  test('JSON button should be disabled without operation selection', async ({ page }) => {
    await navigateToDebrief(page);
    const btn = page.locator('button', { hasText: 'Download Operation JSON' });
    await expect(btn).toBeDisabled({ timeout: 15_000 });
  });

  test('clicking JSON button should trigger JSON API call', async ({ page }) => {
    let jsonRequested = false;
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await page.route('**/plugin/debrief/json', (route) => {
      jsonRequested = true;
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ filename: 'debrief-report', operations: [] }),
      });
    });
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);

    await page.locator('button', { hasText: 'Download Operation JSON' }).click();
    await page.waitForTimeout(2000);
    expect(jsonRequested).toBeTruthy();
  });
});

// ===========================================================================
// 6. D3 graph rendering
// ===========================================================================
test.describe('Debrief D3 graph rendering', () => {
  test('should have SVG containers for all graph types', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('#debrief-steps-svg')).toBeAttached({ timeout: 15_000 });
    await expect(page.locator('#debrief-attackpath-svg')).toBeAttached();
    await expect(page.locator('#debrief-tactic-svg')).toBeAttached();
    await expect(page.locator('#debrief-technique-svg')).toBeAttached();
  });

  test('should have graph type selector with all options', async ({ page }) => {
    await navigateToDebrief(page);
    const graphSelect = page.locator('select', { has: page.locator('option[value="attackpath"]') });
    await expect(graphSelect).toBeAttached({ timeout: 15_000 });
    await expect(page.locator('option[value="steps"]')).toBeAttached();
    await expect(page.locator('option[value="tactic"]')).toBeAttached();
    await expect(page.locator('option[value="technique"]')).toBeAttached();
  });

  test('should have fact graph SVG container', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('#debrief-fact-svg')).toBeAttached({ timeout: 15_000 });
  });

  test('should have playback control buttons', async ({ page }) => {
    await navigateToDebrief(page);
    // Playback buttons: fast-backward, backward, play/pause, forward, fast-forward
    const buttons = page.locator('#debrief-graph .buttons button');
    await expect(buttons).toHaveCount(6, { timeout: 15_000 });
  });

  test('should have a legend toggle button', async ({ page }) => {
    await navigateToDebrief(page);
    const legendBtn = page.locator('button', { hasText: /Legend/ });
    await expect(legendBtn).toBeAttached({ timeout: 15_000 });
  });

  test('graph settings modal should show display options', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);

    await page.locator('button', { hasText: 'Graph Settings' }).click();
    await expect(page.locator('.modal.is-active')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('text=Display Options')).toBeVisible();
    await expect(page.locator('text=Show labels')).toBeVisible();
    await expect(page.locator('text=Show icons')).toBeVisible();
    await expect(page.locator('text=Data Options')).toBeVisible();
    await expect(page.locator('text=Show operation steps')).toBeVisible();
    await expect(page.locator('text=Show steps as tactics')).toBeVisible();
  });
});

// ===========================================================================
// 7. Error states
// ===========================================================================
test.describe('Debrief error states', () => {
  test('should handle no operations gracefully', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    // Heading should still show
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible({ timeout: 15_000 });
    // No options in dropdown
    const options = page.locator('select option:not([disabled])');
    await expect(options).toHaveCount(0);
  });

  test('should handle operations API failure gracefully', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({ status: 500, body: 'Server Error' })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await navigateToDebrief(page);
    // Page should still render without crashing
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible({ timeout: 15_000 });
  });

  test('should handle report API failure gracefully', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({ status: 500, body: 'Report generation failed' })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(2000);
    // Page should not crash
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });

  test('should handle PDF download failure gracefully', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await page.route('**/plugin/debrief/pdf', (route) =>
      route.fulfill({ status: 500, body: 'PDF generation failed' })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);
    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await page.waitForTimeout(500);
    const downloadBtn = page.locator('.modal.is-active button', { hasText: 'Download' });
    await downloadBtn.click();
    await page.waitForTimeout(2000);
    // Page should not crash
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });

  test('should handle JSON export failure gracefully', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_OPERATIONS),
      })
    );
    await page.route('**/plugin/debrief/report', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_REPORT),
      })
    );
    await page.route('**/plugin/debrief/graph**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], links: [] }),
      })
    );
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await page.route('**/plugin/debrief/logos', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ logos: [] }),
      })
    );
    await page.route('**/plugin/debrief/json', (route) =>
      route.fulfill({ status: 500, body: 'JSON export failed' })
    );
    await navigateToDebrief(page);
    const select = page.locator('select').first();
    await select.selectOption({ index: 1 });
    await page.waitForTimeout(1000);
    await page.locator('button', { hasText: 'Download Operation JSON' }).click();
    await page.waitForTimeout(2000);
    // Page should not crash
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });

  test('should handle network timeout on operations API', async ({ page }) => {
    await page.route('**/api/v2/operations', (route) => route.abort('timedout'));
    await page.route('**/plugin/debrief/sections', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_SECTIONS),
      })
    );
    await navigateToDebrief(page);
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible({ timeout: 15_000 });
  });
});
