import type { SharedBoard } from '@/lib/types'
import { compareBoardOrder } from './boardOrder'

export interface BoardChange {
  boardKey: string
  revision: number
  table: string
  operation: 'INSERT' | 'UPDATE' | 'DELETE'
  record: Record<string, unknown> | null
  oldRecord: Record<string, unknown> | null
}

type BoardState = { board: SharedBoard } & Record<string, unknown>
const receivedRevisions = new WeakMap<BoardState, { snapshot: number; records: Map<string, number> }>()

export function mergeBoardChange(state: BoardState, change: BoardChange, onAccepted?: (change: BoardChange) => void): boolean {
  if (change.boardKey !== state.board.key) return false
  const current = state[change.table]
  if (!Array.isArray(current)) return false

  const record = change.record ?? change.oldRecord
  const id = record?.id
  if (typeof id !== 'number') return false

  let received = receivedRevisions.get(state)
  if (!received) { received = { snapshot: state.board.revision, records: new Map() }; receivedRevisions.set(state, received) }
  const revisions = received.records
  const key = `${change.table}:${id}`
  // Reject stale events per record, not globally: a late event for a different
  // row must still be applied.
  if (change.revision <= (revisions.get(key) ?? received.snapshot)) return true
  revisions.set(key, change.revision)
  onAccepted?.(change)

  const removed = change.operation === 'DELETE' || Boolean(change.record?.deleted_at)
  if (removed) {
    state[change.table] = current.filter((item) => (item as { id?: number }).id !== id)
  } else if (change.record) {
    const index = current.findIndex((item) => (item as { id?: number }).id === id)
    if (index >= 0) current[index] = { ...current[index], ...change.record }
    else current.push(change.record)
    if (current.every(item => typeof item.sort_order === 'number')) current.sort(compareBoardOrder)
  }

  state.board.revision = Math.max(state.board.revision, change.revision)
  return true
}
