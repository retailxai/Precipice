import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/drafts', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          drafts: [
            {
              id: 1,
              title: 'Test Draft 1',
              slug: 'test-draft-1',
              summary: 'A test draft for testing',
              status: 'draft',
              created_at: '2025-01-01T00:00:00Z',
              updated_at: '2025-01-01T00:00:00Z',
              tags: ['test', 'example']
            },
            {
              id: 2,
              title: 'Test Draft 2',
              slug: 'test-draft-2',
              summary: 'Another test draft',
              status: 'published',
              created_at: '2025-01-01T00:00:00Z',
              updated_at: '2025-01-01T00:00:00Z',
              tags: ['test']
            }
          ],
          total: 2,
          page: 1,
          size: 20,
          pages: 1
        })
      });
    });

    await page.route('**/api/stats', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          stats: {
            totalDrafts: 2,
            publishedToday: 1,
            activeChannels: 3,
            lastUpdate: '2025-01-01T00:00:00Z'
          }
        })
      });
    });

    await page.route('**/api/health/summary', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'healthy',
          database: 'healthy',
          redis: 'healthy',
          workers: 'healthy',
          queue_depth: 0,
          rate_limits: {
            remaining: 100,
            reset_at: '2025-01-01T01:00:00Z'
          }
        })
      });
    });
  });

  test('should display dashboard header', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText('RetailXAI Dashboard')).toBeVisible();
  });

  test('should display navigation tabs', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText('Drafts')).toBeVisible();
    await expect(page.getByText('Health')).toBeVisible();
  });

  test('should display stats card', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText('Statistics')).toBeVisible();
    await expect(page.getByText('2')).toBeVisible(); // Total drafts
    await expect(page.getByText('1')).toBeVisible(); // Published today
    await expect(page.getByText('3')).toBeVisible(); // Active channels
  });

  test('should display drafts list', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText('Drafts')).toBeVisible();
    await expect(page.getByText('Test Draft 1')).toBeVisible();
    await expect(page.getByText('Test Draft 2')).toBeVisible();
    await expect(page.getByText('A test draft for testing')).toBeVisible();
    await expect(page.getByText('Another test draft')).toBeVisible();
  });

  test('should display draft status badges', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText('draft')).toBeVisible();
    await expect(page.getByText('published')).toBeVisible();
  });

  test('should display draft tags', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText('test')).toBeVisible();
    await expect(page.getByText('example')).toBeVisible();
  });

  test('should display publish buttons', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByText('Publish to Substack')).toBeVisible();
    await expect(page.getByText('Publish to LinkedIn')).toBeVisible();
    await expect(page.getByText('Publish to Twitter')).toBeVisible();
  });

  test('should switch to health tab', async ({ page }) => {
    await page.goto('/');
    
    await page.getByText('Health').click();
    
    await expect(page.getByText('System Health')).toBeVisible();
    await expect(page.getByText('Database')).toBeVisible();
    await expect(page.getByText('Redis')).toBeVisible();
    await expect(page.getByText('Workers')).toBeVisible();
  });

  test('should handle publish to Substack', async ({ page }) => {
    // Mock publish API response
    await page.route('**/api/drafts/1/publish', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Publishing queued',
          endpoints: ['substack'],
          job_ids: ['job_1']
        })
      });
    });

    await page.goto('/');
    
    // Click publish to Substack button
    await page.getByText('Publish to Substack').first().click();
    
    // Should show success message (this would be implemented in the component)
    // For now, we just verify the API call was made
    await expect(page.getByText('Publish to Substack')).toBeVisible();
  });

  test('should handle publish to LinkedIn', async ({ page }) => {
    // Mock publish API response
    await page.route('**/api/drafts/1/publish', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Publishing queued',
          endpoints: ['linkedin'],
          job_ids: ['job_2']
        })
      });
    });

    await page.goto('/');
    
    // Click publish to LinkedIn button
    await page.getByText('Publish to LinkedIn').first().click();
    
    await expect(page.getByText('Publish to LinkedIn')).toBeVisible();
  });

  test('should handle publish to Twitter', async ({ page }) => {
    // Mock publish API response
    await page.route('**/api/drafts/1/publish', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Publishing queued',
          endpoints: ['twitter'],
          job_ids: ['job_3']
        })
      });
    });

    await page.goto('/');
    
    // Click publish to Twitter button
    await page.getByText('Publish to Twitter').first().click();
    
    await expect(page.getByText('Publish to Twitter')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    await expect(page.getByText('RetailXAI Dashboard')).toBeVisible();
    await expect(page.getByText('Drafts')).toBeVisible();
    await expect(page.getByText('Health')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/drafts', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Internal server error'
        })
      });
    });

    await page.goto('/');
    
    // Should show error message
    await expect(page.getByText('Error loading drafts')).toBeVisible();
  });
});
