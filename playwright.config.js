// @ts-check
const { defineConfig, devices } = require('@playwright/test');

const CALDERA_URL = process.env.CALDERA_URL || 'http://localhost:8888';
const CALDERA_USER = process.env.CALDERA_USER || (process.env.CI ? undefined : 'admin');
const CALDERA_PASS = process.env.CALDERA_PASS || (process.env.CI ? undefined : 'admin');

if (process.env.CI && (!CALDERA_USER || !CALDERA_PASS)) {
  throw new Error('CALDERA_USER and CALDERA_PASS must be set in CI');
}

module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 60_000,
  use: {
    baseURL: CALDERA_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    headless: true,
    httpCredentials: {
      username: CALDERA_USER,
      password: CALDERA_PASS,
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
