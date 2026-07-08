import { defineConfig, devices } from '@playwright/test'

/**
 * E2E 测试配置（可选，需先安装：npx playwright install）
 * 运行：npx playwright test
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://127.0.0.1:5174',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'cd app && npm run dev',
    url: 'http://127.0.0.1:5174',
    reuseExistingServer: true,
    timeout: 60000,
  },
})
