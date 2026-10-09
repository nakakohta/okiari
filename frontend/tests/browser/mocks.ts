const channels: Array<MockChannel> = []
export const listeners = new Set<() => void>()
export const writes: Array<Record<string, unknown>> = []
export const records = [
  { id: 3, board_id: 1, store_id: 1, scope: 'drink', item_name: '行3', max_quantity: 0, requested_quantity: 0, note: '', status: 'pending', sort_order: 1 },
  { id: 1, board_id: 1, store_id: 1, scope: 'drink', item_name: '行1', max_quantity: 0, requested_quantity: 0, note: '', status: 'pending', sort_order: 0 },
  { id: 2, board_id: 1, store_id: 1, scope: 'drink', item_name: '行2', max_quantity: 0, requested_quantity: 0, note: '', status: 'pending', sort_order: 1 },
]
let nextId = 3
class MockChannel {
  handler: ((message: unknown) => void) | null = null
  on(_type: string, _filter: unknown, handler: (message: unknown) => void) { this.handler = handler; return this }
  subscribe(handler: (status: string) => void) { queueMicrotask(() => handler('SUBSCRIBED')); return this }
  async send(message: { payload: unknown }) {
    channels.filter(peer => peer !== this).forEach(peer => peer.handler?.({ payload: message.payload }))
    return 'ok'
  }
}
export const supabase = {
  auth: { getSession: async () => ({ data: { session: null } }) },
  realtime: { setAuth: async () => {} },
  channel: () => { const channel = new MockChannel(); channels.push(channel); return channel },
  removeChannel: async () => {},
}
export const boardService = {
  async update(_board: string, _resource: string, id: number, values: Record<string, unknown>) {
    const record = records.find(row => row.id === id)
    if (record) Object.assign(record, values)
    writes.push(values)
    listeners.forEach(refresh => refresh())
    return record
  },
  async create(_board: string, _resource: string, values: Record<string, unknown>) {
    const row = { ...records[0], ...values, id: ++nextId }
    records.push(row)
    listeners.forEach(refresh => refresh())
    return row
  },
}
