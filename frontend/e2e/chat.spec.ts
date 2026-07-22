import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');
  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/GTCC/i);
});

test('can interact with chat input', async ({ page }) => {
  await page.goto('/');
  
  // Wait for the app to load (assuming there's an input field with placeholder "Hỏi lộ trình...")
  const chatInput = page.getByPlaceholder(/hỏi lộ trình/i);
  await expect(chatInput).toBeVisible({ timeout: 15000 });
  
  // Fill the input
  await chatInput.fill('Chào bạn, bạn có thể giúp gì cho tôi?');
  await expect(chatInput).toHaveValue('Chào bạn, bạn có thể giúp gì cho tôi?');
  
  // The actual sending might require auth, so we just test the input for now
});
