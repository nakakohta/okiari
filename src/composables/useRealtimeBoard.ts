import { onMounted, onUnmounted, ref } from 'vue'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import type { BoardKey } from '@/lib/services'
import type { RealtimeConnectionState } from '@/composables/useRealtimeRefresh'

export function useRealtimeBoard(board: BoardKey, refresh: () => Promise<void> | void) {
  const realtimeState = ref<RealtimeConnectionState>('connecting')
  let channel: RealtimeChannel | null = null
  let timer: ReturnType<typeof setTimeout> | null = null

  function scheduleRefresh() {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      void refresh()
    }, 80)
  }

  onMounted(async () => {
    const { data } = await supabase.auth.getSession()
    if (data.session?.access_token) await supabase.realtime.setAuth(data.session.access_token)
    channel = supabase
      .channel(`board:${board}`, { config: { private: true } })
      .on('broadcast', { event: 'changed' }, scheduleRefresh)
      .subscribe((status, error) => {
        if (status === 'SUBSCRIBED') {
          realtimeState.value = 'connected'
          void refresh()
        }
        else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          realtimeState.value = 'error'
          console.error(`Realtime subscription failed for ${board}`, error)
        } else if (status === 'CLOSED') realtimeState.value = 'closed'
      })
  })

  onUnmounted(() => {
    if (timer) clearTimeout(timer)
    if (channel) void supabase.removeChannel(channel)
    realtimeState.value = 'closed'
  })

  return { realtimeState }
}
