import { test, expect } from '@playwright/test';

test.describe('Dashboard Cross-Browser Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('/api/v1/validations*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          validations: [
            {
              id: 'val-001',
              business_concept: 'AI-powered project management tool',
              target_market: 'Small businesses',
              status: 'completed',
              created_at: '2024-01-15T10:30:00Z',
              confidence_score: 0.85,
              overall_score: 78
            }
          ],
          total: 1,
          page: 1,
          page_size: 20
        })
      });
    });

    await page.route('/api/v1/health', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'ok',
          timestamp: new Date().toISOString()
        })
      });
    });

    await page.goto('/');
  });

  test('loads dashboard in all browsers', async ({ page }) => {
    await expect(page.locator('text=RiskIntel360 Platform')).toBeVisible();
    await expect(page.locator('text=Welcome back')).toBeVisible();
  });

  test('navigation works across browsers', async ({ page }) => {
    await expect(page.locator('[role="navigation"]')).toBeVisible();
    await expect(page.locator('text=Dashboard')).toBeVisible();
    await expect(page.locator('text=New Validation')).toBeVisible();
  });

  test('responsive design works on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('text=RiskIntel360')).toBeVisible();
    
    // Check mobile menu
    const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
    if (await mobileMenuButton.isVisible()) {
      await mobileMenuButton.click();
      await expect(page.locator('text=Dashboard')).toBeVisible();
    }
  });

  test('keyboard navigation works', async ({ page }) => {
    // Tab through navigation items
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    const focusedElement = await page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('handles different screen sizes', async ({ page }) => {
    // Test various screen sizes
    const sizes = [
      { width: 1920, height: 1080 }, // Desktop
      { width: 1366, height: 768 },  // Laptop
      { width: 768, height: 1024 },  // Tablet
      { width: 375, height: 667 },   // Mobile
    ];

    for (const size of sizes) {
      await page.setViewportSize(size);
      await expect(page.locator('text=RiskIntel360')).toBeVisible();
    }
  });

  test('visual regression test', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('dashboard.png');
  });

  test('performance metrics', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    // Should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('handles JavaScript disabled', async ({ page, context }) => {
    await context.addInitScript(() => {
      // Disable JavaScript features that might break
      Object.defineProperty(window, 'fetch', { value: undefined });
    });
    
    await page.goto('/');
    // Basic content should still be visible
    await expect(page.locator('text=RiskIntel360')).toBeVisible();
  });
});
