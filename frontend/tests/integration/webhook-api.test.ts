import { describe, it, expect, vi, beforeEach } from 'vitest';
import { POST } from '@/app/api/webhooks/linear/route';
import { NextRequest } from 'next/server';
import crypto from 'crypto';

// Mock WebSocket manager
vi.mock('@/lib/websocket-server', () => ({
  wsManager: {
    broadcast: vi.fn(),
  },
}));

describe('POST /api/webhooks/linear', () => {
  const webhookSecret = 'test-secret';

  beforeEach(() => {
    vi.clearAllMocks();
    process.env.LINEAR_WEBHOOK_SECRET = webhookSecret;
  });

  function createSignature(payload: string): string {
    const hmac = crypto.createHmac('sha256', webhookSecret);
    hmac.update(payload);
    return hmac.digest('hex');
  }

  it('processes issue create webhook', async () => {
    const payload = {
      action: 'create',
      type: 'Issue',
      data: {
        id: 'issue-1',
        title: 'New Task',
        state: { name: 'Todo' },
        priority: 2,
        team: { key: 'DEV' },
      },
      organizationId: 'org-1',
      webhookTimestamp: Date.now(),
      webhookId: 'webhook-1',
    };

    const payloadString = JSON.stringify(payload);
    const signature = createSignature(payloadString);

    const request = new NextRequest('http://localhost:3000/api/webhooks/linear', {
      method: 'POST',
      headers: {
        'linear-signature': signature,
        'content-type': 'application/json',
      },
      body: payloadString,
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.success).toBe(true);

    const { wsManager } = await import('@/lib/websocket-server');
    expect(wsManager.broadcast).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'task.create',
        data: expect.objectContaining({
          id: 'issue-1',
          title: 'New Task',
        }),
      }),
      'DEV'
    );
  });

  it('processes issue update webhook', async () => {
    const payload = {
      action: 'update',
      type: 'Issue',
      data: {
        id: 'issue-1',
        title: 'Updated Task',
        state: { name: 'In Progress' },
        priority: 3,
        team: { key: 'DEV' },
      },
      organizationId: 'org-1',
      webhookTimestamp: Date.now(),
      webhookId: 'webhook-2',
    };

    const payloadString = JSON.stringify(payload);
    const signature = createSignature(payloadString);

    const request = new NextRequest('http://localhost:3000/api/webhooks/linear', {
      method: 'POST',
      headers: {
        'linear-signature': signature,
        'content-type': 'application/json',
      },
      body: payloadString,
    });

    const response = await POST(request);

    expect(response.status).toBe(200);

    const { wsManager } = await import('@/lib/websocket-server');
    expect(wsManager.broadcast).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'task.update',
      }),
      'DEV'
    );
  });

  it('rejects invalid signature', async () => {
    const payload = {
      action: 'create',
      type: 'Issue',
      data: { id: 'issue-1' },
      organizationId: 'org-1',
      webhookTimestamp: Date.now(),
      webhookId: 'webhook-3',
    };

    const payloadString = JSON.stringify(payload);
    // Create invalid signature with correct length (64 hex chars = 32 bytes)
    const invalidSignature = 'a'.repeat(64);

    const request = new NextRequest('http://localhost:3000/api/webhooks/linear', {
      method: 'POST',
      headers: {
        'linear-signature': invalidSignature,
        'content-type': 'application/json',
      },
      body: payloadString,
    });

    const response = await POST(request);

    expect(response.status).toBe(401);
  });

  it('handles missing webhook secret', async () => {
    delete process.env.LINEAR_WEBHOOK_SECRET;

    const payload = { action: 'create', type: 'Issue', data: {} };
    const payloadString = JSON.stringify(payload);

    const request = new NextRequest('http://localhost:3000/api/webhooks/linear', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
      },
      body: payloadString,
    });

    const response = await POST(request);

    expect(response.status).toBe(500);
  });
});
