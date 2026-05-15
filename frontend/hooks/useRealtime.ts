import { useEffect, useRef, useState, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import type { RealtimeChannel } from '@supabase/supabase-js'

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseRealtimeOptions {
  table: string
  filter?: string
  onInsert?: (payload: any) => void
  onUpdate?: (payload: any) => void
  onDelete?: (payload: any) => void
  autoReconnect?: boolean
  maxReconnectAttempts?: number
}

export function useRealtime({
  table,
  filter,
  onInsert,
  onUpdate,
  onDelete,
  autoReconnect = true,
  maxReconnectAttempts = 10,
}: UseRealtimeOptions) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')
  const channelRef = useRef<RealtimeChannel | null>(null)
  const reconnectAttempts = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const baseDelay = 3000 // 3 seconds
  const maxDelay = 30000 // 30 seconds

  const connect = useCallback(() => {
    if (channelRef.current) {
      supabase.removeChannel(channelRef.current)
    }

    setStatus('connecting')

    const channelName = `realtime-${table}-${Date.now()}`
    const channel = supabase.channel(channelName)

    // Subscribe to INSERT events
    if (onInsert) {
      channel.on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table,
          filter,
        },
        (payload) => {
          onInsert(payload.new)
        }
      )
    }

    // Subscribe to UPDATE events
    if (onUpdate) {
      channel.on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table,
          filter,
        },
        (payload) => {
          onUpdate(payload.new)
        }
      )
    }

    // Subscribe to DELETE events
    if (onDelete) {
      channel.on(
        'postgres_changes',
        {
          event: 'DELETE',
          schema: 'public',
          table,
          filter,
        },
        (payload) => {
          onDelete(payload.old)
        }
      )
    }

    channel
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          setStatus('connected')
          reconnectAttempts.current = 0
          console.log(`✅ Connected to ${table} realtime`)
        } else if (status === 'CHANNEL_ERROR') {
          setStatus('error')
          console.error(`❌ Error connecting to ${table} realtime`)

          if (autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
            scheduleReconnect()
          }
        } else if (status === 'TIMED_OUT') {
          setStatus('disconnected')
          console.warn(`⏱️ Connection to ${table} timed out`)

          if (autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
            scheduleReconnect()
          }
        }
      })

    channelRef.current = channel
  }, [table, filter, onInsert, onUpdate, onDelete, autoReconnect, maxReconnectAttempts])

  const scheduleReconnect = useCallback(() => {
    reconnectAttempts.current += 1

    // Exponential backoff: 3s, 6s, 12s, 24s, 30s (max)
    const delay = Math.min(
      baseDelay * Math.pow(1.5, reconnectAttempts.current - 1),
      maxDelay
    )

    console.log(
      `🔄 Reconnecting to ${table} in ${delay / 1000}s (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`
    )

    reconnectTimeoutRef.current = setTimeout(() => {
      connect()
    }, delay)
  }, [table, connect, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (channelRef.current) {
      supabase.removeChannel(channelRef.current)
      channelRef.current = null
    }

    setStatus('disconnected')
    reconnectAttempts.current = 0
  }, [])

  const reconnect = useCallback(() => {
    disconnect()
    reconnectAttempts.current = 0
    connect()
  }, [disconnect, connect])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    status,
    reconnect,
    disconnect,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    isDisconnected: status === 'disconnected',
    isError: status === 'error',
    reconnectAttempts: reconnectAttempts.current,
  }
}
