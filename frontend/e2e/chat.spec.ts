import { test, expect } from '@playwright/test';

test.describe('GTCC Bot - Chat UI/UX', () => {
  test('should display the home page with chat interface', async ({ page }) => {
    await page.goto('/');

    // Check title
    await expect(page).toHaveTitle(/GTCC Bot/);

    // Check empty state
    await expect(page.getByText('Hỏi tôi về tuyến xe buýt, metro hoặc luật giao thông')).toBeVisible();

    // Check input is visible
    const input = page.getByPlaceholder('Nhập câu hỏi của bạn...');
    await expect(input).toBeVisible();

    // Check submit button
    const submitBtn = page.getByRole('button', { name: '' }); // We can add aria-label to the button
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toBeDisabled();
  });

  test('should allow user to type and send a message', async ({ page }) => {
    await page.goto('/');

    const input = page.getByPlaceholder('Nhập câu hỏi của bạn...');
    await input.fill('Cách đi từ Bến Thành đến Suối Tiên');
    
    const submitBtn = page.getByRole('button');
    await expect(submitBtn).toBeEnabled();

    // Mock API response
    await page.route('**/agents/stream', async route => {
      const responseBody = 'data: {"text": "Bạn có thể đi Metro số 1"}\n\n';
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: responseBody,
      });
    });

    await input.press('Enter');

    // The message should appear in chat
    await expect(page.getByText('Cách đi từ Bến Thành đến Suối Tiên')).toBeVisible();
    
    // The bot's response should appear (mocked)
    // Note: ReactMarkdown renders it as a paragraph
    await expect(page.getByText('Bạn có thể đi Metro số 1')).toBeVisible({ timeout: 10000 });
  });
});
