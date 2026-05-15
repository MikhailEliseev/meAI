import { useCallback } from 'react';
import toast from 'react-hot-toast';
import { useWebSocket, WebSocketMessage } from './useWebSocket';

export function useNotifications() {
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'task.create':
        toast.success(
          `New task: ${message.data.title}`,
          {
            duration: 5000,
            icon: '✨',
          }
        );
        break;

      case 'task.update':
        if (message.data.state) {
          const stateEmoji = getStateEmoji(message.data.state);
          toast(
            `Task updated: ${message.data.title || 'Task'} → ${message.data.state}`,
            {
              duration: 4000,
              icon: stateEmoji,
            }
          );
        } else if (message.data.commentAdded) {
          toast(
            `New comment on: ${message.data.title || 'Task'}`,
            {
              duration: 4000,
              icon: '💬',
            }
          );
        }
        break;

      case 'project.update':
        toast(
          `Project updated: ${message.data.name}`,
          {
            duration: 4000,
            icon: '📊',
          }
        );
        break;

      case 'ping':
        // Silent ping, no notification
        break;

      default:
        console.log('[Notifications] Unknown message type:', message.type);
    }
  }, []);

  const handleConnect = useCallback(() => {
    toast.success('Connected to real-time updates', {
      duration: 2000,
      icon: '🔌',
    });
  }, []);

  const handleDisconnect = useCallback(() => {
    toast.error('Disconnected from real-time updates', {
      duration: 3000,
      icon: '🔌',
    });
  }, []);

  const handleError = useCallback(() => {
    toast.error('Connection error. Retrying...', {
      duration: 3000,
      icon: '⚠️',
    });
  }, []);

  const ws = useWebSocket({
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
  });

  return ws;
}

function getStateEmoji(state: string): string {
  const stateLower = state.toLowerCase();

  if (stateLower.includes('done') || stateLower.includes('completed')) {
    return '✅';
  }
  if (stateLower.includes('progress') || stateLower.includes('started')) {
    return '🚀';
  }
  if (stateLower.includes('review')) {
    return '👀';
  }
  if (stateLower.includes('blocked')) {
    return '🚫';
  }
  if (stateLower.includes('backlog') || stateLower.includes('todo')) {
    return '📋';
  }

  return '🔄';
}
