import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  return new Response(
    JSON.stringify({
      error: 'WebSocket endpoint',
      message: 'Use WebSocket protocol to connect to this endpoint'
    }),
    {
      status: 426,
      headers: {
        'Content-Type': 'application/json',
        'Upgrade': 'websocket'
      }
    }
  );
}
