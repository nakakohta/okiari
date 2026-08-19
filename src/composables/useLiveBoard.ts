import { inject, nextTick, onMounted, onUnmounted, provide, shallowRef } from 'vue'
import type { ShallowRef } from 'vue'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { boardService, type BoardKey, type BoardResource } from '@/lib/services'
import { supabase } from '@/lib/supabase'

export interface LiveFieldRelations {
  row_id?: number
  column_id?: number
}

export interface LiveFieldChange {
  type: 'field_changed'
  resource: BoardResource
  recordId: number
  field: string
  value: unknown
  revision: number
  clientId: string
  clientSeq: number
  relations?: LiveFieldRelations
}

interface PendingEdit {
  change: LiveFieldChange
  timer: ReturnType<typeof setTimeout>
}

type FieldHandler = (change: LiveFieldChange) => void

export interface LiveBoardContext {
  cancel(resource: BoardResource, recordId: number): void
  edit(resource: BoardResource, recordId: number, field: string, value: unknown, relations?: LiveFieldRelations): void
  getValue(resource: BoardResource, recordId: number, field: string, relations?: LiveFieldRelations): unknown
  hasPending(resource: BoardResource, recordId: number, field: string, relations?: LiveFieldRelations): boolean
  lastChange: ShallowRef<LiveFieldChange | null>
  subscribe(handler: FieldHandler): () => void
}

const liveBoardKey = Symbol('live-board')

function fieldKey(resource: BoardResource, recordId: number, field: string, relations?: LiveFieldRelations) {
  if (resource === 'md-cells' && relations?.row_id && relations.column_id) {
    return `${resource}:${relations.row_id}:${relations.column_id}:${field}`
  }
  return `${resource}:${recordId}:${field}`
}

function transformedPosition(position: number, before: string, after: string) {
  let prefix = 0
  while (prefix < before.length && prefix < after.length && before[prefix] === after[prefix]) prefix += 1
  let suffix = 0
  while (
    suffix < before.length - prefix
    && suffix < after.length - prefix
    && before[before.length - suffix - 1] === after[after.length - suffix - 1]
  ) suffix += 1
  if (position <= prefix) return position
  if (position >= before.length - suffix) return Math.max(0, position + after.length - before.length)
  return Math.min(after.length - suffix, prefix + Math.max(0, after.length - prefix - suffix))
}

async function preserveActiveSelection(key: string, before: unknown, after: unknown) {
  if (typeof before !== 'string' || typeof after !== 'string') return
  const active = document.activeElement
  if (!(active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement)) return
  if (active.dataset.liveField !== key) return
  const start = active.selectionStart
  const end = active.selectionEnd
  if (start === null || end === null) return
  await nextTick()
  if (document.activeElement !== active) return
  active.setSelectionRange(
    transformedPosition(start, before, after),
    transformedPosition(end, before, after),
  )
}

export function provideLiveBoard(board: BoardKey, refresh: () => Promise<void> | void) {
  const clientId = crypto.randomUUID()
  const lastChange = shallowRef<LiveFieldChange | null>(null)
  const handlers = new Set<FieldHandler>()
  const revisions = new Map<string, number>()
  const values = new Map<string, unknown>()
  const pending = new Map<string, PendingEdit>()
  const deferred = new Map<string, LiveFieldChange>()
  const queued = new Map<string, LiveFieldChange>()
  let channel: RealtimeChannel | null = null
  let clientSeq = 0
  let ready = false

  function apply(change: LiveFieldChange, key: string) {
    const before = values.get(key)
    values.set(key, change.value)
    if (change.resource === 'md-cells' && change.recordId > 0 && change.relations) {
      values.set(`${change.resource}:${change.recordId}:${change.field}`, change.value)
    }
    lastChange.value = change
    for (const handler of handlers) handler(change)
    void preserveActiveSelection(key, before, change.value)
  }

  function processChange(change: LiveFieldChange) {
    if (!change || change.type !== 'field_changed' || change.clientId === clientId) return
    const key = fieldKey(change.resource, change.recordId, change.field, change.relations)
    if (change.revision <= (revisions.get(key) ?? 0)) return
    revisions.set(key, change.revision)
    const outstanding = pending.get(key)
    if (outstanding) {
      if (change.revision > outstanding.change.revision) deferred.set(key, change)
      return
    }
    apply(change, key)
  }

  function broadcast(change: LiveFieldChange) {
    if (!ready || !channel) {
      queued.set(fieldKey(change.resource, change.recordId, change.field, change.relations), change)
      return
    }
    void channel.send({ type: 'broadcast', event: 'field_changed', payload: change })
  }

  async function persist(key: string, edit: PendingEdit) {
    const { change } = edit
    try {
      if (change.resource === 'md-cells' && change.relations) {
        if (change.recordId > 0) {
          await boardService.update(board, change.resource, change.recordId, { [change.field]: change.value })
        } else {
          const created = await boardService.create<{ id: number }>(board, change.resource, {
            ...change.relations,
            [change.field]: change.value,
          })
          change.recordId = created.id
        }
      } else {
        await boardService.update(board, change.resource, change.recordId, { [change.field]: change.value })
      }
      if (pending.get(key) === edit) pending.delete(key)
      const held = deferred.get(key)
      if (held && held.revision > change.revision) apply(held, key)
      deferred.delete(key)
    } catch (error) {
      console.error(`Live field persistence failed for ${key}`, error)
      if (pending.get(key) === edit) pending.delete(key)
      deferred.delete(key)
      void refresh()
    }
  }

  function cancelMatching(predicate: (key: string) => boolean) {
    for (const [key, edit] of pending) {
      if (!predicate(key)) continue
      clearTimeout(edit.timer)
      pending.delete(key)
    }
    for (const collection of [revisions, values, deferred, queued]) {
      for (const key of collection.keys()) if (predicate(key)) collection.delete(key)
    }
  }

  const context: LiveBoardContext = {
    edit(resource, recordId, field, value, relations) {
      const key = fieldKey(resource, recordId, field, relations)
      const previous = pending.get(key)
      if (previous) clearTimeout(previous.timer)
      const sequence = ++clientSeq
      const change: LiveFieldChange = {
        type: 'field_changed',
        resource,
        recordId,
        field,
        value,
        revision: Date.now() * 1_000 + sequence % 1_000,
        clientId,
        clientSeq: sequence,
        ...(relations ? { relations } : {}),
      }
      values.set(key, value)
      revisions.set(key, change.revision)
      const edit: PendingEdit = {
        change,
        timer: setTimeout(() => void persist(key, edit), 300),
      }
      pending.set(key, edit)
      broadcast(change)
    },
    cancel(resource, recordId) {
      cancelMatching((key) => key.startsWith(`${resource}:${recordId}:`))
    },
    getValue(resource, recordId, field, relations) {
      const key = fieldKey(resource, recordId, field, relations)
      if (values.has(key)) return values.get(key)
      if (resource === 'md-cells' && recordId > 0 && relations) return values.get(`${resource}:${recordId}:${field}`)
      return undefined
    },
    hasPending(resource, recordId, field, relations) {
      return pending.has(fieldKey(resource, recordId, field, relations))
    },
    lastChange,
    subscribe(handler) {
      handlers.add(handler)
      return () => handlers.delete(handler)
    },
  }

  provide(liveBoardKey, context)
  onMounted(async () => {
    const { data } = await supabase.auth.getSession()
    if (data.session?.access_token) await supabase.realtime.setAuth(data.session.access_token)
    channel = supabase
      .channel(`board:${board}:live`, { config: { private: true } })
      .on('broadcast', { event: 'field_changed' }, (message) => processChange(message.payload as LiveFieldChange))
      .subscribe((status, error) => {
        if (status === 'SUBSCRIBED') {
          ready = true
          for (const change of queued.values()) broadcast(change)
          queued.clear()
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          ready = false
          console.error(`Live field subscription failed for ${board}`, error)
        } else if (status === 'CLOSED') {
          ready = false
        }
      })
  })
  onUnmounted(() => {
    ready = false
    for (const [key, edit] of pending) {
      clearTimeout(edit.timer)
      void persist(key, edit)
    }
    if (channel) void supabase.removeChannel(channel)
    handlers.clear()
  })
  return context
}

export function useLiveBoard() {
  return inject<LiveBoardContext | null>(liveBoardKey, null)
}

export function liveFieldKey(resource: BoardResource, recordId: number, field: string, relations?: LiveFieldRelations) {
  return fieldKey(resource, recordId, field, relations)
}
