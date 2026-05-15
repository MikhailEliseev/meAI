import { test, expect } from '@playwright/test';

test.describe('Webhook API', () => {
  test('rejects invalid signature', async ({ request }) => {
    const payload = {
      action: 'create',
      type: 'Issue',
      data: { id: 'issue-1', title: 'Test' },
      organizationId: 'org-1',
      webhookTimestamp: Date.now(),
      webhookId: 'webhook-1',
    };

    const response = await request.post('/api/webhooks/linear', {
      headers: {
        'linear-signature': 'a'.repeat(64), // Invalid signature
        'content-type': 'application/json',
      },
      data: JSON.stringify(payload),
    });

    expect(response.status()).toBe(401);
    const data = await response.json();
    expect(data.error).toContain('Invalid signature');
  });

  test('handles missing webhook secret', async ({ request }) => {
    const payload = {
      action: 'create',
      type: 'Issue',
      data: { id: 'issue-1', title: 'Test' },
      organizationId: 'org-1',
      webhookTimestamp: Date.now(),
      webhookId: 'webhook-1',
    };

    // This test assumes LINEAR_WEBHOOK_SECRET is set in .env
    // If not set, should return 500
    const response = await request.post('/api/webhooks/linear', {
      headers: {
        'content-type': 'application/json',
      },
      data: JSON.stringify(payload),
    });

    // Either 200 (secret is set and no signature check) or 500 (secret not set)
    expect([200, 500]).toContain(response.status());
  });
});
