import { onMounted, onUnmounted, ref } from 'vue'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

export type RealtimeConnectionState = 'connecting' | 'connected' | 'error' | 'closed'

let channelSequence = 0

export function useRealtimeRefresh(table: string, refresh: () => Promise<void> | void) {
  const state = ref<RealtimeConnectionState>('connecting')
  let channel: RealtimeChannel | null = null
  let refreshTimer: ReturnType<typeof setTimeout> | null = null

  function scheduleRefresh() {
    if (refreshTimer) clearTimeout(refreshTimer)
    refreshTimer = setTimeout(() => {
      refreshTimer = null
      void refresh()
    }, 80)
  }

  onMounted(() => {
    const sequence = channelSequence++
    channel = supabase
      .channel(`db-${table}-${sequence}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table },
        scheduleRefresh,
      )
      .subscribe((status, error) => {
        if (status === 'SUBSCRIBED') {
          state.value = 'connected'
          return
        }
        if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          state.value = 'error'
          console.error(`Realtime subscription failed for ${table}`, error)
          return
        }
        if (status === 'CLOSED') state.value = 'closed'
      })
  })

  onUnmounted(() => {
    if (refreshTimer) clearTimeout(refreshTimer)
    if (channel) void supabase.removeChannel(channel)
    state.value = 'closed'
  })

  return { realtimeState: state }
}
