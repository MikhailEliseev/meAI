import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';
import { wsManager } from '@/lib/websocket-server';

interface LinearWebhookPayload {
  action: 'create' | 'update' | 'remove';
  type: 'Issue' | 'Project' | 'Comment';
  data: any;
  organizationId: string;
  webhookTimestamp: number;
  webhookId: string;
}

function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload);
  const expectedSignature = hmac.digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

export async function POST(request: NextRequest) {
  try {
    const signature = request.headers.get('linear-signature');
    const webhookSecret = process.env.LINEAR_WEBHOOK_SECRET;

    if (!webhookSecret) {
      console.error('[Webhook] LINEAR_WEBHOOK_SECRET not configured');
      return NextResponse.json(
        { error: 'Webhook secret not configured' },
        { status: 500 }
      );
    }

    const body = await request.text();

    // Verify signature
    if (signature) {
      try {
        if (!verifyWebhookSignature(body, signature, webhookSecret)) {
          console.error('[Webhook] Invalid signature');
          return NextResponse.json(
            { error: 'Invalid signature' },
            { status: 401 }
          );
        }
      } catch (error) {
        console.error('[Webhook] Signature verification failed:', error);
        return NextResponse.json(
          { error: 'Invalid signature' },
          { status: 401 }
        );
      }
    }

    const payload: LinearWebhookPayload = JSON.parse(body);

    console.log('[Webhook] Received:', {
      action: payload.action,
      type: payload.type,
      webhookId: payload.webhookId
    });

    // Process webhook based on type
    if (payload.type === 'Issue') {
      await handleIssueWebhook(payload);
    } else if (payload.type === 'Project') {
      await handleProjectWebhook(payload);
    } else if (payload.type === 'Comment') {
      await handleCommentWebhook(payload);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('[Webhook] Error processing webhook:', error);
    return NextResponse.json(
      { error: 'Failed to process webhook' },
      { status: 500 }
    );
  }
}

async function handleIssueWebhook(payload: LinearWebhookPayload) {
  const { action, data } = payload;

  // Extract tenant ID from project or team
  const tenantId = data.team?.key || 'default';

  if (action === 'create') {
    wsManager.broadcast(
      {
        type: 'task.create',
        data: {
          id: data.id,
          title: data.title,
          state: data.state?.name,
          priority: data.priority,
          assignee: data.assignee?.name,
          project: data.project?.name,
        },
        timestamp: new Date().toISOString()
      },
      tenantId
    );
  } else if (action === 'update') {
    wsManager.broadcast(
      {
        type: 'task.update',
        data: {
          id: data.id,
          title: data.title,
          state: data.state?.name,
          priority: data.priority,
          assignee: data.assignee?.name,
          project: data.project?.name,
          updatedAt: data.updatedAt,
        },
        timestamp: new Date().toISOString()
      },
      tenantId
    );
  }

  console.log(`[Webhook] Broadcasted ${action} for issue ${data.id} to tenant ${tenantId}`);
}

async function handleProjectWebhook(payload: LinearWebhookPayload) {
  const { action, data } = payload;
  const tenantId = data.team?.key || 'default';

  if (action === 'update') {
    wsManager.broadcast(
      {
        type: 'project.update',
        data: {
          id: data.id,
          name: data.name,
          state: data.state,
          progress: data.progress,
          updatedAt: data.updatedAt,
        },
        timestamp: new Date().toISOString()
      },
      tenantId
    );
  }

  console.log(`[Webhook] Broadcasted ${action} for project ${data.id} to tenant ${tenantId}`);
}

async function handleCommentWebhook(payload: LinearWebhookPayload) {
  const { action, data } = payload;

  // Comments are associated with issues
  if (data.issue) {
    const tenantId = data.issue.team?.key || 'default';

    wsManager.broadcast(
      {
        type: 'task.update',
        data: {
          id: data.issue.id,
          commentAdded: true,
          comment: {
            id: data.id,
            body: data.body,
            user: data.user?.name,
            createdAt: data.createdAt,
          },
        },
        timestamp: new Date().toISOString()
      },
      tenantId
    );

    console.log(`[Webhook] Broadcasted comment for issue ${data.issue.id} to tenant ${tenantId}`);
  }
}
