# WebSocket Real-Time Updates

## Overview

The application uses WebSocket connections to provide real-time updates from Linear webhooks. When tasks or projects change in Linear, updates are instantly pushed to all connected clients.

## Architecture

```
Linear Webhook → API Route → WebSocket Server → Connected Clients
     ↓              ↓              ↓                    ↓
  Signature    Broadcast to    Tenant-based      React Hooks
  Validation    wsManager       Filtering         Update UI
```

## Components

### 1. WebSocket Server (`lib/websocket-server.ts`)

Custom WebSocket server that runs alongside Next.js:

```typescript
import { wsManager } from '@/lib/websocket-server';

// Server automatically initializes in server.ts
wsManager.initialize(server);

// Broadcast to all clients
wsManager.broadcast({
  type: 'task.update',
  data: { id: '123', title: 'Updated Task' },
  timestamp: new Date().toISOString()
});

// Broadcast to specific tenant
wsManager.broadcast(message, 'tenant-id');
```

**Features:**
- Automatic heartbeat (30s interval)
- Tenant-based message filtering
- Connection lifecycle management
- Graceful shutdown handling

### 2. Custom Next.js Server (`server.ts`)

Combines HTTP and WebSocket servers:

```typescript
import { createServer } from 'http';
import next from 'next';
import { wsManager } from './lib/websocket-server';

const server = createServer(async (req, res) => {
  await handle(req, res, parsedUrl);
});

wsManager.initialize(server);
server.listen(port);
```

**Start server:**
```bash
npm run dev    # Development with hot reload
npm start      # Production
```

### 3. Webhook Handler (`app/api/webhooks/linear/route.ts`)

Receives Linear webhooks and broadcasts to WebSocket clients:

```typescript
export async function POST(request: NextRequest) {
  // 1. Verify HMAC signature
  const signature = request.headers.get('linear-signature');
  if (!verifyWebhookSignature(body, signature, secret)) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
  }

  // 2. Parse payload
  const payload: LinearWebhookPayload = JSON.parse(body);

  // 3. Broadcast to WebSocket clients
  wsManager.broadcast({
    type: 'task.update',
    data: payload.data,
    timestamp: new Date().toISOString()
  }, tenantId);

  return NextResponse.json({ success: true });
}
```

### 4. React Hooks

#### `useWebSocket` - Connection Management

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

function MyComponent() {
  const { status, isConnected, send, connect, disconnect } = useWebSocket({
    onConnect: () => console.log('Connected'),
    onMessage: (message) => console.log('Received:', message),
    onDisconnect: () => console.log('Disconnected'),
  });

  return (
    <div>
      Status: {status}
      {!isConnected && <button onClick={connect}>Connect</button>}
    </div>
  );
}
```

**Features:**
- Auto-connect on session availability
- Exponential backoff reconnection (max 10 attempts)
- Heartbeat with server ping/pong
- Connection status tracking

#### `useNotifications` - Toast Notifications

```typescript
import { useNotifications } from '@/hooks/useNotifications';

function MyComponent() {
  useNotifications(); // Automatically shows toasts for WebSocket events

  return <div>...</div>;
}
```

**Notification Types:**
- ✨ New task created
- 📝 Task updated
- ✅ Task completed (state: Done)
- 🚀 Task in progress
- 👀 Task in review
- 🔄 Project updated

#### `useProjects` / `useIssues` - Real-Time Data

```typescript
import { useProjects } from '@/hooks/useProjects';

function ProjectsList() {
  const { projects, loading, error, refetch } = useProjects();

  // Projects automatically update via WebSocket
  return (
    <div>
      {projects.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

**Features:**
- Optimistic UI updates
- Automatic refetch on WebSocket reconnect
- Real-time synchronization with Linear

### 5. WebSocket Provider (`components/dashboard/WebSocketProvider.tsx`)

Dashboard-level provider with connection status indicator:

```tsx
import { WebSocketProvider } from '@/components/dashboard/WebSocketProvider';

export default function DashboardLayout({ children }) {
  return (
    <WebSocketProvider>
      {children}
    </WebSocketProvider>
  );
}
```

Shows connection status in bottom-right corner:
- 🔄 Connecting...
- ❌ Connection error

## Message Types

### Task Events

```typescript
// Task created
{
  type: 'task.create',
  data: {
    id: string,
    title: string,
    state: string,
    priority: number,
    assignee?: string,
    project?: string,
  },
  timestamp: string
}

// Task updated
{
  type: 'task.update',
  data: {
    id: string,
    title?: string,
    state?: string,
    priority?: number,
    assignee?: string,
    updatedAt: string,
  },
  timestamp: string
}
```

### Project Events

```typescript
// Project updated
{
  type: 'project.update',
  data: {
    id: string,
    name?: string,
    state?: string,
    progress?: number,
    updatedAt: string,
  },
  timestamp: string
}
```

## Configuration

### Environment Variables

```bash
# .env.local
LINEAR_WEBHOOK_SECRET=your_webhook_secret_here
LINEAR_API_KEY=your_api_key_here
```

### Linear Webhook Setup

1. Go to Linear Settings → API → Webhooks
2. Create new webhook
3. URL: `https://your-domain.com/api/webhooks/linear`
4. Secret: Generate and save to `LINEAR_WEBHOOK_SECRET`
5. Events: Select `Issue`, `Project`, `Comment`

## Security

### Signature Verification

All webhooks are verified using HMAC SHA256:

```typescript
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
```

### Tenant Isolation

Messages are filtered by tenant ID:

```typescript
// Only clients with matching tenantId receive the message
wsManager.broadcast(message, 'tenant-123');
```

## Monitoring

### Connection Stats

```typescript
const stats = wsManager.getStats();
console.log(stats);
// {
//   totalConnections: 5,
//   activeConnections: 3,
//   tenants: ['tenant-1', 'tenant-2']
// }
```

### Health Check

```typescript
// Check if WebSocket server is running
const isHealthy = wsManager.wss !== null;
```

## Troubleshooting

### WebSocket connection fails

1. Check server is running: `npm run dev`
2. Check port 3000 is not blocked
3. Check browser console for errors
4. Verify `ws://localhost:3000` is accessible

### Messages not received

1. Check webhook signature is valid
2. Check `LINEAR_WEBHOOK_SECRET` is set
3. Check tenant ID matches
4. Check WebSocket connection status

### Reconnection issues

1. Check network connectivity
2. Check server logs for errors
3. Verify exponential backoff is working
4. Check max reconnection attempts (10)

## Development

### Testing WebSocket Locally

```bash
# Terminal 1: Start server
npm run dev

# Terminal 2: Send test webhook
curl -X POST http://localhost:3000/api/webhooks/linear \
  -H "Content-Type: application/json" \
  -H "linear-signature: $(echo -n '{"action":"create","type":"Issue","data":{"id":"test-1","title":"Test"}}' | openssl dgst -sha256 -hmac 'your-secret' | cut -d' ' -f2)" \
  -d '{"action":"create","type":"Issue","data":{"id":"test-1","title":"Test"},"organizationId":"org-1","webhookTimestamp":1234567890,"webhookId":"webhook-1"}'
```

### Debugging

Enable debug logs:

```typescript
// In useWebSocket.ts
console.log('[WebSocket] Status:', status);
console.log('[WebSocket] Message:', message);

// In websocket-server.ts
console.log('[WebSocket] Client connected:', clientId);
console.log('[WebSocket] Broadcasting:', message);
```

## Performance

### Connection Limits

- Max connections per server: ~10,000
- Heartbeat interval: 30s
- Reconnection backoff: 1s → 2s → 4s → 8s → 16s → 30s (max)

### Message Size

- Max message size: 1MB (configurable)
- Recommended: Keep messages < 10KB

### Scaling

For production with multiple servers:

1. Use Redis pub/sub for cross-server messaging
2. Implement sticky sessions for WebSocket connections
3. Use load balancer with WebSocket support (nginx, HAProxy)

## Resources

- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Linear Webhooks](https://developers.linear.app/docs/graphql/webhooks)
- [Next.js Custom Server](https://nextjs.org/docs/advanced-features/custom-server)
