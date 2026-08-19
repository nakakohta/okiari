import { inject, nextTick, onMounted, onUnmounted, provide, shallowRef } from 'vue'
import type { ShallowRef } from 'vue'
import { boardService, type BoardKey, type BoardResource } from '@/lib/services'
import { boardWebSocketUrl } from '@/lib/apiBase'

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
  actorId?: string | null
  clientId?: string | null
  clientSeq?: number | null
  relations?: LiveFieldRelations
}

interface PendingEdit {
  clientSeq: number
  message: Record<string, unknown>
}

interface UnpersistedEdit extends PendingEdit {
  actualRecordId: number
  confirmedRevision?: number
  field: string
  resource: BoardResource
}

type FieldHandler = (change: LiveFieldChange) => void

export interface LiveBoardContext {
  cancel(resource: BoardResource, recordId: number): void
  edit(
    resource: BoardResource,
    recordId: number,
    field: string,
    value: unknown,
    relations?: LiveFieldRelations,
  ): void
  getValue(
    resource: BoardResource,
    recordId: number,
    field: string,
    relations?: LiveFieldRelations,
  ): unknown
  hasPending(
    resource: BoardResource,
    recordId: number,
    field: string,
    relations?: LiveFieldRelations,
  ): boolean
  lastChange: ShallowRef<LiveFieldChange | null>
  subscribe(handler: FieldHandler): () => void
}

const liveBoardKey = Symbol('live-board')

function fieldKey(
  resource: BoardResource,
  recordId: number,
  field: string,
  relations?: LiveFieldRelations,
) {
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
  const unpersisted = new Map<string, UnpersistedEdit>()
  const deferred = new Map<string, LiveFieldChange>()
  const queued = new Map<string, Record<string, unknown>>()
  let socket: WebSocket | null = null
  let clientSeq = 0
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempt = 0
  let ready = false
  let stopped = false

  function removeTarget(target: {
    resource: BoardResource
    recordId: number
    field?: string
    relations?: LiveFieldRelations
  }) {
    const matches = (key: string) => {
      const parts = key.split(':')
      const fieldMatches = !target.field || parts.at(-1) === target.field
      if (parts[0] === target.resource && Number(parts[1]) === target.recordId && fieldMatches) return true
      if (parts[0] !== 'md-cells') return false
      if (target.resource === 'md-rows' && Number(parts[1]) === target.recordId && fieldMatches) return true
      if (target.resource === 'md-columns' && Number(parts[2]) === target.recordId && fieldMatches) return true
      return target.resource === 'md-cells'
        && Number(parts[1]) === target.relations?.row_id
        && Number(parts[2]) === target.relations?.column_id
        && fieldMatches
    }
    for (const collection of [revisions, values, pending, unpersisted, deferred, queued]) {
      for (const key of collection.keys()) if (matches(key)) collection.delete(key)
    }
  }

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
    const key = fieldKey(change.resource, change.recordId, change.field, change.relations)
    if (change.revision <= (revisions.get(key) ?? 0)) return
    revisions.set(key, change.revision)
    const outstanding = pending.get(key)
    const own = change.clientId === clientId

    if (own) {
      const durable = unpersisted.get(key)
      if (durable && durable.clientSeq === change.clientSeq) {
        durable.actualRecordId = change.recordId
        durable.confirmedRevision = change.revision
      }
    }

    if (own && outstanding) {
      const acknowledged = change.clientSeq ?? 0
      if (acknowledged < outstanding.clientSeq) return
      pending.delete(key)
      const held = deferred.get(key)
      deferred.delete(key)
      if (held && held.revision > change.revision) apply(held, key)
      else apply(change, key)
      return
    }

    if (outstanding) {
      const held = deferred.get(key)
      if (!held || held.revision < change.revision) deferred.set(key, change)
      return
    }
    apply(change, key)
  }

  function flushQueue() {
    if (!ready || socket?.readyState !== WebSocket.OPEN) return
    for (const message of queued.values()) socket.send(JSON.stringify(message))
    queued.clear()
  }

  function scheduleReconnect() {
    if (stopped || reconnectTimer) return
    const delay = Math.min(10_000, 500 * 2 ** Math.min(reconnectAttempt, 4))
    reconnectAttempt += 1
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      void connect()
    }, delay)
  }

  async function connect() {
    if (stopped || socket?.readyState === WebSocket.OPEN || socket?.readyState === WebSocket.CONNECTING) return
    try {
      const { ticket } = await boardService.collaborationTicket(board)
      if (stopped) return
      socket = new WebSocket(boardWebSocketUrl(board))
      socket.addEventListener('open', () => {
        socket?.send(JSON.stringify({ type: 'authenticate', ticket }))
      })
      socket.addEventListener('message', (event) => {
        const message = JSON.parse(String(event.data)) as Record<string, unknown>
        if (message.type === 'sync' && Array.isArray(message.values)) {
          for (const item of message.values) processChange(item as LiveFieldChange)
          ready = true
          reconnectAttempt = 0
          flushQueue()
          return
        }
        if (message.type === 'field_changed') {
          processChange(message as unknown as LiveFieldChange)
          return
        }
        if (message.type === 'field_persisted') {
          for (const [key, edit] of unpersisted) {
            if (
              edit.resource === message.resource
              && edit.actualRecordId === message.recordId
              && edit.field === message.field
              && edit.confirmedRevision !== undefined
              && edit.confirmedRevision <= Number(message.revision)
            ) unpersisted.delete(key)
          }
          return
        }
        if (message.type === 'field_error') {
          const resource = message.resource as BoardResource
          const recordId = Number(message.recordId)
          const field = String(message.field ?? '')
          const relations = message.relations as LiveFieldRelations | undefined
          const key = fieldKey(resource, recordId, field, relations)
          const outstanding = pending.get(key)
          const rejectedSequence = Number(message.clientSeq ?? 0)
          if (outstanding && rejectedSequence < outstanding.clientSeq) return
          pending.delete(key)
          unpersisted.delete(key)
          deferred.delete(key)
          queued.delete(key)
          const current = message.current as LiveFieldChange | null | undefined
          if (current) {
            const currentKey = fieldKey(current.resource, current.recordId, current.field, current.relations)
            revisions.set(currentKey, Math.max(revisions.get(currentKey) ?? 0, current.revision))
            apply(current, currentKey)
          } else {
            revisions.delete(key)
            values.delete(key)
          }
          void refresh()
          return
        }
        if (message.type === 'board_reset') {
          revisions.clear()
          values.clear()
          pending.clear()
          unpersisted.clear()
          deferred.clear()
          queued.clear()
          void refresh()
          return
        }
        if (message.type === 'structure_changed' || message.type === 'fields_reset') {
          const targets = Array.isArray(message.targets)
            ? message.targets
            : [{ resource: message.resource, recordId: message.recordId }]
          for (const target of targets) {
            if (!target || typeof target !== 'object') continue
            const item = target as Record<string, unknown>
            if (typeof item.resource !== 'string' || typeof item.recordId !== 'number') continue
            removeTarget({
              resource: item.resource as BoardResource,
              recordId: item.recordId,
              field: typeof item.field === 'string' ? item.field : undefined,
              relations: item.relations as LiveFieldRelations | undefined,
            })
          }
          void refresh()
        }
      })
      socket.addEventListener('close', () => {
        for (const [key, edit] of unpersisted) {
          pending.set(key, edit)
          queued.set(key, edit.message)
        }
        ready = false
        socket = null
        scheduleReconnect()
      })
      socket.addEventListener('error', () => socket?.close())
    } catch {
      scheduleReconnect()
    }
  }

  const context: LiveBoardContext = {
    edit(resource, recordId, field, value, relations) {
      const key = fieldKey(resource, recordId, field, relations)
      const sequence = ++clientSeq
      const message: Record<string, unknown> = {
        type: 'field_edit',
        board,
        resource,
        recordId,
        field,
        value,
        clientId,
        clientSeq: sequence,
      }
      if (relations) message.relations = relations
      values.set(key, value)
      pending.set(key, { clientSeq: sequence, message })
      unpersisted.set(key, {
        clientSeq: sequence,
        message,
        resource,
        field,
        actualRecordId: recordId,
      })
      if (ready && socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(message))
      else queued.set(key, message)
    },
    cancel(resource, recordId) {
      const prefix = `${resource}:${recordId}:`
      for (const collection of [revisions, values, pending, unpersisted, deferred, queued]) {
        for (const key of collection.keys()) if (key.startsWith(prefix)) collection.delete(key)
      }
    },
    getValue(resource, recordId, field, relations) {
      const key = fieldKey(resource, recordId, field, relations)
      if (values.has(key)) return values.get(key)
      if (resource === 'md-cells' && recordId > 0 && relations) {
        return values.get(`${resource}:${recordId}:${field}`)
      }
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
  onMounted(() => void connect())
  onUnmounted(() => {
    stopped = true
    ready = false
    if (reconnectTimer) clearTimeout(reconnectTimer)
    socket?.close()
    socket = null
    handlers.clear()
  })
  return context
}

export function useLiveBoard() {
  return inject<LiveBoardContext | null>(liveBoardKey, null)
}

export function liveFieldKey(
  resource: BoardResource,
  recordId: number,
  field: string,
  relations?: LiveFieldRelations,
) {
  return fieldKey(resource, recordId, field, relations)
}
