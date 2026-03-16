// @ts-check
const { test, expect } = require('@playwright/test');

const PLUGIN_ROUTE = '/#/plugins/debrief';

// ---------------------------------------------------------------------------
// Shared mock data
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Mock all standard debrief API routes. Pass `overrides` to replace or add
 * route handlers (keyed by glob pattern).
 */
async function mockDebriefRoutes(page, overrides = {}) {
  const defaults = {
    '**/api/v2/operations': (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_OPERATIONS) }),
    '**/plugin/debrief/report': (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_REPORT) }),
    '**/plugin/debrief/graph**': (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ nodes: [], links: [] }) }),
    '**/plugin/debrief/sections': (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SECTIONS) }),
    '**/plugin/debrief/logos': (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ logos: [] }) }),
  };
  const routes = { ...defaults, ...overrides };
  for (const [pattern, handler] of Object.entries(routes)) {
    await page.route(pattern, handler);
  }
}

/** Navigate to the debrief plugin page and wait for the heading to appear. */
async function navigateToDebrief(page) {
  await page.goto(PLUGIN_ROUTE, { waitUntil: 'domcontentloaded' });
  await page.locator('h2', { hasText: 'Debrief' }).waitFor({ state: 'visible', timeout: 15_000 });
}

/** Select the first operation from the dropdown and wait for the report to load. */
async function selectFirstOperation(page) {
  const select = page.locator('select').first();
  await select.selectOption({ index: 1 });
  // Wait for the report API response to arrive
  await page.waitForResponse((resp) => resp.url().includes('/plugin/debrief/report'), { timeout: 10_000 }).catch(() => {});
}

// ===========================================================================
// 1. Plugin page loads
// ===========================================================================
test.describe('Debrief plugin page load', () => {
  test('should display the Debrief heading', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });

  test('should display campaign analytics description', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('text=Campaign Analytics')).toBeVisible({ timeout: 15_000 });
  });

  test('should render Graph Settings button', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('button', { hasText: 'Graph Settings' })).toBeVisible({ timeout: 15_000 });
  });

  test('should render Download PDF Report button', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('button', { hasText: 'Download PDF Report' })).toBeVisible({ timeout: 15_000 });
  });

  test('should render Download Operation JSON button', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('button', { hasText: 'Download Operation JSON' })).toBeVisible({ timeout: 15_000 });
  });

  test('should have an operation select dropdown', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('select').first()).toBeVisible({ timeout: 15_000 });
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
  test('buttons should be disabled when no operation is selected', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('button', { hasText: 'Download PDF Report' })).toBeDisabled({ timeout: 15_000 });
    await expect(page.locator('button', { hasText: 'Download Operation JSON' })).toBeDisabled();
    await expect(page.locator('button', { hasText: 'Graph Settings' })).toBeDisabled();
  });

  test('operations dropdown should populate from API', async ({ page }) => {
    await mockDebriefRoutes(page);
    await navigateToDebrief(page);
    const options = page.locator('select option');
    // 1 disabled placeholder + 2 mock operations
    await expect(options).toHaveCount(3, { timeout: 15_000 });
  });

  test('selecting an operation should trigger report loading', async ({ page }) => {
    let reportRequested = false;
    await mockDebriefRoutes(page, {
      '**/plugin/debrief/report': (route) => {
        reportRequested = true;
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_REPORT) });
      },
    });
    await navigateToDebrief(page);
    await selectFirstOperation(page);
    expect(reportRequested).toBeTruthy();
  });
});

// ===========================================================================
// 3. Report section display (tabs: stats, agents, steps, tactics, facts)
// ===========================================================================
test.describe('Debrief report section display', () => {
  test('should show tabs when an operation is selected', async ({ page }) => {
    await mockDebriefRoutes(page);
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await expect(page.locator('a', { hasText: 'Stats' })).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('a', { hasText: 'Agents' })).toBeVisible();
    await expect(page.locator('a', { hasText: 'Steps' })).toBeVisible();
    await expect(page.locator('a', { hasText: 'Tactics & Techniques' })).toBeVisible();
    await expect(page.locator('a', { hasText: 'Fact Graph' })).toBeVisible();
  });

  test('Stats tab should show operation statistics table headers', async ({ page }) => {
    await mockDebriefRoutes(page);
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await expect(page.locator('th', { hasText: 'Name' }).first()).toBeVisible({ timeout: 10_000 });
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
    await expect(page.locator('button', { hasText: 'Download PDF Report' })).toBeDisabled({ timeout: 15_000 });
  });

  test('clicking PDF button should open report modal', async ({ page }) => {
    await mockDebriefRoutes(page);
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await expect(page.locator('.modal.is-active')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('text=Download Report as PDF')).toBeVisible();
  });

  test('report modal should have Report Sections heading', async ({ page }) => {
    await mockDebriefRoutes(page);
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await expect(page.locator('h5', { hasText: 'Report Sections' })).toBeVisible({ timeout: 5_000 });
  });

  test('report modal should show custom logo checkbox', async ({ page }) => {
    await mockDebriefRoutes(page);
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await expect(page.locator('text=Use custom logo')).toBeVisible({ timeout: 5_000 });
  });

  test('report modal Download button triggers PDF API call', async ({ page }) => {
    let pdfRequested = false;
    await mockDebriefRoutes(page, {
      '**/plugin/debrief/pdf': (route) => {
        pdfRequested = true;
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ filename: 'debrief-report.pdf', pdf_bytes: '' }) });
      },
    });
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await page.locator('.modal.is-active').waitFor({ state: 'visible', timeout: 5_000 });
    const downloadBtn = page.locator('.modal.is-active button', { hasText: 'Download' });
    await downloadBtn.click();
    await page.waitForResponse((resp) => resp.url().includes('/plugin/debrief/pdf'), { timeout: 10_000 }).catch(() => {});
    expect(pdfRequested).toBeTruthy();
  });
});

// ===========================================================================
// 5. JSON export
// ===========================================================================
test.describe('Debrief JSON export', () => {
  test('JSON button should be disabled without operation selection', async ({ page }) => {
    await navigateToDebrief(page);
    await expect(page.locator('button', { hasText: 'Download Operation JSON' })).toBeDisabled({ timeout: 15_000 });
  });

  test('clicking JSON button should trigger JSON API call', async ({ page }) => {
    let jsonRequested = false;
    await mockDebriefRoutes(page, {
      '**/plugin/debrief/json': (route) => {
        jsonRequested = true;
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ filename: 'debrief-report', operations: [] }) });
      },
    });
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await page.locator('button', { hasText: 'Download Operation JSON' }).click();
    await page.waitForResponse((resp) => resp.url().includes('/plugin/debrief/json'), { timeout: 10_000 }).catch(() => {});
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
    // Playback buttons: fast-backward, backward, play/pause, forward, fast-forward, plus legend toggle
    const buttons = page.locator('#debrief-graph .buttons button');
    await expect(buttons).toHaveCount(6, { timeout: 15_000 });
  });

  test('should have a legend toggle button', async ({ page }) => {
    await navigateToDebrief(page);
    const legendBtn = page.locator('button', { hasText: /Legend/ });
    await expect(legendBtn).toBeAttached({ timeout: 15_000 });
  });

  test('graph settings modal should show display options', async ({ page }) => {
    await mockDebriefRoutes(page);
    await navigateToDebrief(page);
    await selectFirstOperation(page);

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
    await mockDebriefRoutes(page, {
      '**/api/v2/operations': (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) }),
    });
    await navigateToDebrief(page);
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
    const options = page.locator('select option:not([disabled])');
    await expect(options).toHaveCount(0);
  });

  test('should handle operations API failure gracefully', async ({ page }) => {
    await mockDebriefRoutes(page, {
      '**/api/v2/operations': (route) =>
        route.fulfill({ status: 500, body: 'Server Error' }),
    });
    await navigateToDebrief(page);
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });

  test('should handle report API failure gracefully', async ({ page }) => {
    await mockDebriefRoutes(page, {
      '**/plugin/debrief/report': (route) =>
        route.fulfill({ status: 500, body: 'Report generation failed' }),
    });
    await navigateToDebrief(page);
    await selectFirstOperation(page);
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });

  test('should handle PDF download failure gracefully', async ({ page }) => {
    await mockDebriefRoutes(page, {
      '**/plugin/debrief/pdf': (route) =>
        route.fulfill({ status: 500, body: 'PDF generation failed' }),
    });
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await page.locator('button', { hasText: 'Download PDF Report' }).click();
    await page.locator('.modal.is-active').waitFor({ state: 'visible', timeout: 5_000 });
    const downloadBtn = page.locator('.modal.is-active button', { hasText: 'Download' });
    await downloadBtn.click();
    await page.waitForResponse((resp) => resp.url().includes('/plugin/debrief/pdf'), { timeout: 10_000 }).catch(() => {});
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });

  test('should handle JSON export failure gracefully', async ({ page }) => {
    await mockDebriefRoutes(page, {
      '**/plugin/debrief/json': (route) =>
        route.fulfill({ status: 500, body: 'JSON export failed' }),
    });
    await navigateToDebrief(page);
    await selectFirstOperation(page);

    await page.locator('button', { hasText: 'Download Operation JSON' }).click();
    await page.waitForResponse((resp) => resp.url().includes('/plugin/debrief/json'), { timeout: 10_000 }).catch(() => {});
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });

  test('should handle network timeout on operations API', async ({ page }) => {
    await mockDebriefRoutes(page, {
      '**/api/v2/operations': (route) => route.abort('timedout'),
    });
    await navigateToDebrief(page);
    await expect(page.locator('h2', { hasText: 'Debrief' })).toBeVisible();
  });
});
