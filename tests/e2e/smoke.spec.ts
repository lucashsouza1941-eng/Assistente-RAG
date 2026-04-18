import { test, expect } from '@playwright/test'

test('página principal carrega sem erro de servidor (sem 500, sem erro crítico visível)', async ({
  page,
}) => {
  const response = await page.goto('/', { waitUntil: 'load' })
  expect(response).toBeTruthy()
  expect(response!.status()).not.toBe(500)

  await expect(page.getByRole('heading', { name: 'OdontoBot' })).toBeVisible({ timeout: 30_000 })

  const bodyText = await page.locator('body').innerText()
  expect(bodyText).not.toMatch(/Internal Server Error|Application error|Unhandled Runtime Error/i)
})
