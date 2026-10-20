import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { test } from 'node:test'
import ts from 'typescript'

const root = path.resolve(import.meta.dirname, '..')
function load(file, mocks = {}, globals = {}) {
  const module = { exports: {} }
  const source = ts.transpileModule(fs.readFileSync(path.join(root, file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText
  vm.runInNewContext(source, {
    module, exports: module.exports, console, setTimeout, clearTimeout,
    ...globals,
    require: name => {
      if (name in mocks) return mocks[name]
      if (name.startsWith('./')) return load(path.join(path.dirname(file), name + '.ts'), mocks, globals)
      throw new Error('Unexpected dependency: ' + name)
    },
  }, { filename: file })
  return module.exports
}
const order = load('src/lib/boardOrder.ts')
const { mergeBoardChange } = load('src/lib/boardRealtime.ts')
const { readInputValue } = load('src/lib/liveInput.ts')
const ids = records => Array.from(records, record => record.id)

test('concurrent equal-rank inserts and full reloads have the same order', () => {
  const left = { board: { key: 'drink-refill', revision: 0 }, dtable_rows: [{ id: 1, sort_order: 0 }] }
  const right = structuredClone(left)
  const changes = [2, 3].map(id => ({ boardKey: 'drink-refill', revision: id, table: 'dtable_rows', operation: 'INSERT', record: { id, sort_order: 1 }, oldRecord: null }))
  changes.forEach(change => mergeBoardChange(left, change))
  changes.toReversed().forEach(change => mergeBoardChange(right, change))
  assert.deepEqual(ids(left.dtable_rows), [1, 2, 3])
  assert.deepEqual(ids(right.dtable_rows), [1, 2, 3])
  assert.deepEqual(ids([...right.dtable_rows].reverse().sort(order.compareBoardOrder)), [1, 2, 3])
})
test('late updates do not resurrect deleted rows but different-row events survive', () => {
  const state = { board: { key: 'drink-refill', revision: 0 }, dtable_rows: [{ id: 1, sort_order: 0 }] }
  const change = (id, revision, deleted_at = null) => ({ boardKey: 'drink-refill', revision, table: 'dtable_rows', operation: 'UPDATE', record: { id, sort_order: 0, deleted_at }, oldRecord: null })
  mergeBoardChange(state, change(1, 10, 'deleted'))
  mergeBoardChange(state, change(1, 9))
  mergeBoardChange(state, change(2, 8))
  assert.deepEqual(ids(state.dtable_rows), [2])
})
test('append uses maximum rank, not count after deletions', () => {
  assert.equal(order.nextBoardOrder([{ id: 1, sort_order: 0 }, { id: 3, sort_order: 8 }]), 9)
})
test('drag remains attached to IDs when another user adds or removes a row', () => {
  const rows = [{ id: 4, sort_order: 0 }, { id: 1, sort_order: 1 }, { id: 3, sort_order: 2 }]
  const moved = order.moveBoardRecord(rows, 1, 3)
  assert.deepEqual(ids(moved), [4, 3, 1])
  assert.deepEqual(ids([...moved].sort(order.compareBoardOrder)), [4, 3, 1])
  assert.equal(order.moveBoardRecord(rows, 2, 3), null)
})
test('input value comes from DOM, including uncommitted Japanese and empty numbers', () => {
  assert.equal(readInputValue({ target: { type: 'text', value: 'おちゃ' } }), 'おちゃ')
  assert.equal(readInputValue({ target: { type: 'number', value: '' } }), '')
  assert.equal(readInputValue({ target: { type: 'number', value: '12' } }), 12)
})

async function clients(service) {
  const channels = []
  const timers = new Map()
  let timerId = 0, clientId = 0
  const globals = {
    document: { activeElement: null }, HTMLInputElement: class {}, HTMLTextAreaElement: class {},
    crypto: { randomUUID: () => 'client-' + ++clientId },
    setTimeout: callback => { timers.set(++timerId, callback); return timerId },
    clearTimeout: id => timers.delete(id),
  }
  const supabase = {
    auth: { getSession: async () => ({ data: { session: null } }) },
    realtime: { setAuth: async () => {} },
    channel: () => {
      const channel = {
        on(_type, _filter, handler) { this.handler = handler; return this },
        subscribe(handler) { this.status = handler; handler('SUBSCRIBED'); return this },
        async send(message) { channels.filter(peer => peer !== this).forEach(peer => peer.handler({ payload: message.payload })); return 'ok' },
      }
      channels.push(channel)
      return channel
    },
    removeChannel: async () => {},
  }
  async function create() {
    const mounted = []
    const vue = { provide() {}, inject() {}, shallowRef: value => ({ value }), nextTick: async () => {}, onMounted: fn => mounted.push(fn), onUnmounted() {} }
    const { provideLiveBoard } = load('src/composables/useLiveBoard.ts', {
      vue, axios: { isAxiosError: () => false }, '@/lib/services': { boardService: service }, '@/lib/supabase': { supabase },
    }, globals)
    const context = provideLiveBoard('drink-refill', () => {})
    await Promise.all(mounted.map(fn => fn()))
    return context
  }
  const tick = async () => {
    const tasks = [...timers.values()]; timers.clear(); tasks.forEach(fn => fn())
    for (let i = 0; i < 8; i++) await Promise.resolve()
  }
  return { left: await create(), right: await create(), tick, channels }
}
test('IME previews reflect before Enter; only committed text is saved', async () => {
  const writes = []
  const { left, right, tick } = await clients({ update: async (...args) => writes.push(args) })
  left.preview('d-rows', 12, 'item_name', 'お')
  assert.equal(right.getValue('d-rows', 12, 'item_name'), 'お')
  left.preview('d-rows', 12, 'item_name', 'おちゃ')
  assert.equal(right.getValue('d-rows', 12, 'item_name'), 'おちゃ')
  await tick(); assert.equal(writes.length, 0)
  left.edit('d-rows', 12, 'item_name', 'お茶')
  assert.equal(right.getValue('d-rows', 12, 'item_name'), 'お茶')
  await tick(); assert.equal(writes.length, 1)
  assert.equal(writes[0][3].item_name, 'お茶')
})
test('Backspace and edits on different row IDs are broadcast immediately', async () => {
  const { left, right } = await clients({ update: async () => {} })
  left.edit('d-rows', 1, 'item_name', 'abc')
  left.edit('d-rows', 1, 'item_name', 'ab')
  left.edit('d-rows', 2, 'item_name', 'other')
  assert.equal(right.getValue('d-rows', 1, 'item_name'), 'ab')
  assert.equal(right.getValue('d-rows', 2, 'item_name'), 'other')
})
test('slow saves are serialized and cannot roll back newer typing', async () => {
  const writes = []
  let release
  const { left, right, tick } = await clients({ update: async (_b, _r, _id, values) => { writes.push(values); if (writes.length === 1) await new Promise(resolve => { release = resolve }) } })
  left.edit('d-rows', 1, 'item_name', 'a'); await tick()
  right.edit('d-rows', 1, 'item_name', 'remote')
  right.cancel('d-rows', 1) // Isolate the remote notification from its DB request.
  left.edit('d-rows', 1, 'item_name', 'abc'); await tick()
  assert.equal(writes.length, 1)
  release(); await tick()
  assert.equal(writes.length, 2)
  assert.equal(writes[1].item_name, 'abc')
  assert.equal(left.getValue('d-rows', 1, 'item_name'), 'abc')
})
test('deleted records discard queued edits and blur flushes final input', async () => {
  const writes = []
  const { left, tick } = await clients({ update: async (...args) => writes.push(args) })
  left.edit('d-rows', 1, 'item_name', 'discard'); left.cancel('d-rows', 1); await tick()
  assert.equal(writes.length, 0)
  left.edit('d-rows', 2, 'item_name', 'saved'); left.flush('d-rows', 2, 'item_name')
  assert.equal(writes.length, 1)
})
test('DB acknowledgement retires the preview; older DB updates cannot erase newer input', async () => {
  const { left } = await clients({ update: async () => {} })
  left.edit('d-rows', 2, 'item_name', 'new')
  const change = value => ({ table: 'dtable_rows', operation: 'UPDATE', record: { id: 2, item_name: value }, oldRecord: null })
  left.reconcile(change('old'))
  assert.equal(left.getValue('d-rows', 2, 'item_name'), 'new')
  left.reconcile(change('new'))
  assert.equal(left.getValue('d-rows', 2, 'item_name'), undefined)
})
test('deleting MD row or column also cancels unsaved cell creation', async () => {
  const writes = []
  const { left, tick } = await clients({ create: async (...args) => { writes.push(args); return { id: 9 } } })
  left.edit('md-cells', 0, 'value', '1', { row_id: 2, column_id: 3 })
  left.cancel('md-columns', 3); await tick()
  assert.equal(writes.length, 0)
})
