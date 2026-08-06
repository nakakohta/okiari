<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { boardService } from '@/lib/services'
import type { DTableLock, DTableRow } from '@/lib/types'

const props = defineProps<{
  title: string
  storeId: number
  scope: 'drink' | 'consumable'
  rows: DTableRow[]
  locks: DTableLock[]
  readonly: boolean
  canManageLocks: boolean
  canDelete: boolean
}>()
const emit = defineEmits<{ refresh: []; error: [message: string] }>()

type EditableField = 'item_name' | 'max_quantity' | 'requested_quantity' | 'note'
type Column = 'status' | 'name' | 'max_quantity' | 'requested_quantity' | 'note'
const localRows = ref<DTableRow[]>([])
const prepareMode = ref(false)
const selected = ref<DTableRow | null>(null)
const modeMessage = ref('')
const pending = new Set<string>()
const timers = new Map<string, ReturnType<typeof setTimeout>>()
const composing = new Set<string>()

const visibleRows = computed(() => prepareMode.value
  ? localRows.value.filter((row) => row.status !== 'completed')
  : localRows.value)

watch(() => props.rows, (rows) => {
  localRows.value = rows.map((incoming) => {
    const current = localRows.value.find((row) => row.id === incoming.id)
    if (!current) return { ...incoming }
    const merged = { ...incoming }
    for (const field of ['item_name', 'max_quantity', 'requested_quantity', 'note'] as EditableField[]) {
      if (pending.has(`${incoming.id}:${field}`)) merged[field] = current[field] as never
    }
    return merged
  })
}, { immediate: true, deep: true })

function locked(column: Column) {
  return props.locks.some((lock) => lock.column_key === column && lock.is_locked)
}

function editable(column: Column) {
  return !props.readonly && !locked(column)
}

function flash(message: string) {
  modeMessage.value = message
  setTimeout(() => { modeMessage.value = '' }, 2600)
}

function togglePrepareMode() {
  prepareMode.value = !prepareMode.value
  flash(prepareMode.value
    ? '売店準備モードです。未補充の行だけを表示します。'
    : '興行日モードに戻りました。')
}

async function save(row: DTableRow, field: EditableField) {
  const key = `${row.id}:${field}`
  const scheduled = timers.get(key)
  if (scheduled) clearTimeout(scheduled)
  timers.delete(key)
  try {
    if (field === 'max_quantity' || field === 'requested_quantity') row[field] = Math.max(0, Number(row[field]) || 0)
    await boardService.update('drink-refill', 'd-rows', row.id, { [field]: row[field] })
    pending.delete(key)
    emit('refresh')
  } catch {
    emit('error', '入力内容を保存できませんでした。接続復旧後にもう一度入力してください。')
    timers.set(key, setTimeout(() => void save(row, field), 2000))
  }
}

function schedule(row: DTableRow, field: EditableField) {
  const key = `${row.id}:${field}`
  if (composing.has(key)) return
  pending.add(key)
  const timer = timers.get(key)
  if (timer) clearTimeout(timer)
  timers.set(key, setTimeout(() => void save(row, field), 450))
}

function composition(row: DTableRow, field: EditableField, active: boolean) {
  const key = `${row.id}:${field}`
  if (active) composing.add(key)
  else {
    composing.delete(key)
    schedule(row, field)
  }
}

async function setStatus(status: DTableRow['status']) {
  if (!selected.value) return
  const row = selected.value
  row.status = status
  selected.value = null
  try {
    await boardService.update('drink-refill', 'd-rows', row.id, { status })
    emit('refresh')
  } catch { emit('error', '補充状況を保存できませんでした。') }
}

async function addRow() {
  try {
    await boardService.create('drink-refill', 'd-rows', {
      store_id: props.storeId, scope: props.scope, item_name: '', max_quantity: 0,
      requested_quantity: 0, note: '', status: 'pending', sort_order: localRows.value.length,
    })
    emit('refresh')
  } catch { emit('error', '行を追加できませんでした。') }
}

async function removeRow(row: DTableRow) {
  if (!confirm('この行を削除しますか？')) return
  try { await boardService.remove('drink-refill', 'd-rows', row.id); emit('refresh') }
  catch { emit('error', '行を削除できませんでした。') }
}

async function toggleLock(column: Column) {
  if (!props.canManageLocks) return
  try {
    await boardService.lock('drink-refill', {
      store_id: props.storeId, scope: props.scope, column_key: column, is_locked: !locked(column),
    })
    emit('refresh')
  } catch { emit('error', '列のロックを変更できませんでした。') }
}

async function clearData() {
  if (!confirm('補充状況・取ってくる数・備考をクリアしますか？')) return
  try { await boardService.clear('drink-refill', { store_id: props.storeId, scope: props.scope }); prepareMode.value = false; emit('refresh') }
  catch { emit('error', '表をクリアできませんでした。') }
}

function flush() {
  for (const [key, timer] of timers) {
    clearTimeout(timer)
    const [idText, field] = key.split(':') as [string, EditableField]
    const row = localRows.value.find((item) => item.id === Number(idText))
    if (row) void save(row, field)
  }
}
onBeforeUnmount(flush)
</script>

<template>
  <div class="d-table">
    <div v-if="modeMessage" class="popup">{{ modeMessage }}</div>
    <div class="header">
      <h3>{{ title }}</h3>
      <div class="actions">
        <button class="prepare" :class="{ active: prepareMode }" @click="togglePrepareMode">
          {{ prepareMode ? '売店準備' : '興行日' }}
        </button>
        <button v-if="canDelete" class="clear" @click="clearData">クリア</button>
      </div>
    </div>
    <div class="toolbar"><button :disabled="readonly" @click="addRow">＋行追加</button></div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th v-for="column in ([['status','補充状況'],['name','商品名'],['max_quantity','売店内MAX'],['requested_quantity','取ってくる数'],['note','備考']] as const)" :key="column[0]">
            {{ column[1] }}
            <button class="lock" :disabled="!canManageLocks" @click="toggleLock(column[0])">{{ locked(column[0]) ? '🔒' : '🔓' }}</button>
          </th><th v-if="canDelete"></th>
        </tr></thead>
        <tbody>
          <tr v-for="row in visibleRows" :key="row.id">
            <td><button class="status" :class="row.status" :disabled="!editable('status')" @click="selected = row">
              {{ row.status === 'pending' ? '未補充' : row.status === 'out_of_stock' ? '在庫無い為未補充' : '完了' }}
            </button></td>
            <td><input v-model="row.item_name" :disabled="!editable('name')" @input="schedule(row,'item_name')" @blur="save(row,'item_name')" @compositionstart="composition(row,'item_name',true)" @compositionend="composition(row,'item_name',false)" /></td>
            <td><input v-model.number="row.max_quantity" type="number" min="0" :disabled="!editable('max_quantity')" @input="schedule(row,'max_quantity')" @blur="save(row,'max_quantity')" /></td>
            <td><input v-model.number="row.requested_quantity" type="number" min="0" :disabled="!editable('requested_quantity')" @input="schedule(row,'requested_quantity')" @blur="save(row,'requested_quantity')" /></td>
            <td><input v-model="row.note" :disabled="!editable('note')" @input="schedule(row,'note')" @blur="save(row,'note')" @compositionstart="composition(row,'note',true)" @compositionend="composition(row,'note',false)" /></td>
            <td v-if="canDelete"><button class="delete" @click="removeRow(row)">削除</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="selected" class="modal-backdrop" @click.self="selected = null">
      <div class="modal"><h4>補充状況を選択</h4>
        <button @click="setStatus('pending')">未補充</button>
        <button @click="setStatus('out_of_stock')">在庫無い為未補充</button>
        <button @click="setStatus('completed')">完了</button>
        <button class="cancel" @click="selected = null">キャンセル</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.d-table{position:relative;margin-bottom:28px}.header,.actions,.toolbar{display:flex;align-items:center}.header{justify-content:space-between;gap:16px}.header h3{font-size:20px}.actions{gap:8px}.toolbar{margin:10px 0}.toolbar button,.prepare,.clear{border:0;border-radius:8px;padding:9px 14px;font-weight:700;cursor:pointer}.toolbar button{background:#2563eb;color:#fff}.prepare{background:#e2e8f0}.prepare.active{background:#f59e0b;color:#fff}.clear,.delete{background:#fee2e2;color:#b91c1c}.table-wrap{overflow:auto}table{width:100%;min-width:850px;border-collapse:collapse}th,td{border:1px solid #dbe4ee;padding:8px;text-align:center}th{background:#f8fafc}.lock{border:0;background:transparent;cursor:pointer}input{box-sizing:border-box;width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:8px}.status{width:100%;border:0;border-radius:18px;padding:8px;font-weight:700;cursor:pointer}.status.pending{background:#fef3c7;color:#92400e}.status.out_of_stock{background:#fee2e2;color:#b91c1c}.status.completed{background:#dcfce7;color:#166534}.delete{border:0;border-radius:6px;padding:7px}.popup{position:fixed;top:24px;left:50%;z-index:1000;transform:translateX(-50%);background:#172033;color:white;padding:12px 20px;border-radius:8px}.modal-backdrop{position:fixed;inset:0;z-index:1100;display:grid;place-items:center;background:#0007}.modal{display:grid;gap:10px;width:min(360px,90vw);padding:24px;border-radius:14px;background:white}.modal button{padding:12px;border:0;border-radius:8px}.cancel{background:#e2e8f0}button:disabled,input:disabled{cursor:not-allowed;opacity:.55}
</style>
