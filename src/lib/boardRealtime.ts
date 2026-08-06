import type { SharedBoard } from '@/lib/types'

export interface BoardChange {
  boardKey: string
  revision: number
  table: string
  operation: 'INSERT' | 'UPDATE' | 'DELETE'
  record: Record<string, unknown> | null
  oldRecord: Record<string, unknown> | null
}

type BoardState = { board: SharedBoard } & Record<string, unknown>

export function mergeBoardChange(state: BoardState, change: BoardChange): boolean {
  if (change.boardKey !== state.board.key) return false
  const current = state[change.table]
  if (!Array.isArray(current)) return false

  const record = change.record ?? change.oldRecord
  const id = record?.id
  if (typeof id !== 'number') return false

  const removed = change.operation === 'DELETE' || Boolean(change.record?.deleted_at)
  if (removed) {
    state[change.table] = current.filter((item) => (item as { id?: number }).id !== id)
  } else if (change.record) {
    const index = current.findIndex((item) => (item as { id?: number }).id === id)
    if (index >= 0) current[index] = change.record
    else current.push(change.record)
  }

  state.board.revision = Math.max(state.board.revision, change.revision)
  return true
}
