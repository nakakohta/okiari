export interface OrderedRecord { id: number; sort_order: number }

// Concurrent additions can share a rank. Use the DB ID, never arrival order,
// as the tie-breaker on every client (and after a full reload).
export function compareBoardOrder(a: OrderedRecord, b: OrderedRecord) {
  return a.sort_order - b.sort_order || a.id - b.id
}

export function nextBoardOrder(records: readonly OrderedRecord[]) {
  return records.reduce((next, record) => Math.max(next, record.sort_order + 1), 0)
}

export function moveBoardRecord<T extends OrderedRecord>(records: readonly T[], sourceId: number, targetId: number): T[] | null {
  const ordered = [...records].sort(compareBoardOrder)
  const source = ordered.findIndex(record => record.id === sourceId)
  const target = ordered.findIndex(record => record.id === targetId)
  if (source < 0 || target < 0 || source === target) return null
  const [moved] = ordered.splice(source, 1)
  ordered.splice(target, 0, moved!)
  return ordered.map((record, sort_order) => ({ ...record, sort_order }))
}
