/**
 * E2E happy-path tests.
 *
 * Prerequisites (handled by CI, or run manually):
 *   make dev        — all services running
 *   make migrate    — tables exist
 *   make seed       — admin + analyst + seed data exist
 *
 * Accounts used:
 *   admin:   admin@example.com  / changeme123!
 *   analyst: analyst@example.com / Analystpass1!
 */

import { test, expect } from '@playwright/test'

const ADMIN_EMAIL = 'admin@example.com'
const ADMIN_PASSWORD = 'changeme123!'
const ANALYST_EMAIL = 'analyst@example.com'
const ANALYST_PASSWORD = 'Analystpass1!'

// ── helpers ───────────────────────────────────────────────────────────────────

async function login(page: import('@playwright/test').Page, email: string, password: string) {
  await page.goto('/login')
  await page.fill('#email', email)
  await page.fill('#password', password)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard')
}

// ── tests ─────────────────────────────────────────────────────────────────────

test.describe('Authentication', () => {
  test('login page renders and rejects bad credentials', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveTitle(/AI Infra/i)
    await expect(page.locator('#email')).toBeVisible()

    await page.fill('#email', 'bad@example.com')
    await page.fill('#password', 'wrongpassword')
    await page.click('button[type="submit"]')

    await expect(page.locator('text=Invalid email or password')).toBeVisible()
  })

  test('admin can log in and reaches dashboard', async ({ page }) => {
    await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.locator('text=Overview')).toBeVisible()
  })

  test('unauthenticated visit to /dashboard redirects to /login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })
})

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  })

  test('shows KPI cards', async ({ page }) => {
    await expect(page.locator('[data-testid="kpi-card"]').first()).toBeVisible({ timeout: 8000 })
  })

  test('sidebar navigation links are present', async ({ page }) => {
    await expect(page.locator('text=Hardware Products')).toBeVisible()
    await expect(page.locator('text=Companies')).toBeVisible()
    await expect(page.locator('text=Research Notes')).toBeVisible()
    await expect(page.locator('text=Sources')).toBeVisible()
    await expect(page.locator('a[href="/search"]')).toBeVisible()
  })

  test('admin sees User Management in sidebar', async ({ page }) => {
    await expect(page.locator('text=User Management')).toBeVisible()
  })
})

test.describe('Search', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, ANALYST_EMAIL, ANALYST_PASSWORD)
  })

  test('navigating to /search shows the search input', async ({ page }) => {
    await page.click('a[href="/search"]')
    await expect(page).toHaveURL(/\/search/)
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible()
  })

  test('searching for "H100" returns results', async ({ page }) => {
    // Navigate via sidebar click to avoid auth rehydration on full page reload
    await page.click('a[href="/search"]')
    await expect(page).toHaveURL(/\/search/)
    await page.fill('input[placeholder*="Search"]', 'H100')
    await page.keyboard.press('Enter')
    // Wait for results (debounced 400ms + network)
    await page.waitForTimeout(1000)
    await expect(page.locator('text=H100').first()).toBeVisible({ timeout: 8000 })
  })
})

test.describe('Admin User Management', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  })

  test('admin can navigate to /admin/users', async ({ page }) => {
    await page.click('text=User Management')
    await expect(page).toHaveURL(/\/admin\/users/)
    await expect(page.locator('[data-testid="admin-users-page"]')).toBeVisible()
  })

  test('users table shows at least the admin user', async ({ page }) => {
    await page.click('text=User Management')
    await expect(page.locator('[data-testid="users-table"]')).toBeVisible({ timeout: 8000 })
    await expect(page.locator(`text=${ADMIN_EMAIL}`)).toBeVisible()
  })

  test('invite modal opens and shows email field', async ({ page }) => {
    await page.click('text=User Management')
    await page.click('[data-testid="invite-user-button"]')
    await expect(page.locator('[data-testid="invite-modal"]')).toBeVisible()
    await expect(page.locator('[data-testid="invite-email-input"]')).toBeVisible()
  })
})

test.describe('Analyst RBAC', () => {
  test('analyst is redirected away from /admin/users', async ({ page }) => {
    await login(page, ANALYST_EMAIL, ANALYST_PASSWORD)

    // Intercept the silent-refresh calls that fire on the full-page reload below.
    // The test is verifying AdminRoute RBAC logic, not the auth mechanism itself,
    // so we stub the two auth endpoints to reliably restore an analyst session.
    await page.route('**/api/v1/auth/refresh', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'stub-access-token',
          refresh_token: 'stub-refresh-token',
          token_type: 'bearer',
        }),
      })
    )
    await page.route('**/api/v1/me', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '00000000-0000-0000-0000-000000000002',
          email: ANALYST_EMAIL,
          role: 'analyst',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
        }),
      })
    )

    await page.goto('/admin/users')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 8000 })
  })

  test('analyst does not see User Management in sidebar', async ({ page }) => {
    await login(page, ANALYST_EMAIL, ANALYST_PASSWORD)
    await expect(page.locator('text=User Management')).not.toBeVisible()
  })
})

test.describe('Accept Invite page', () => {
  test('loads without token and shows error message', async ({ page }) => {
    await page.goto('/accept-invite')
    await expect(page.locator('text=Invalid invite link')).toBeVisible()
  })

  test('loads with token and shows password form', async ({ page }) => {
    await page.goto('/accept-invite?token=some-fake-token-for-ui-test')
    await expect(page.locator('[data-testid="accept-invite-form"]')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
  })
})
