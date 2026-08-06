<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { boardService } from '@/lib/services'
import type { MDTableCell, MDTableColumn, MDTableLock, MDTableRow } from '@/lib/types'

const props = defineProps<{
  title: string
  floorGroup: 'first' | 'second' | 'third'
  rows: MDTableRow[]
  columns: MDTableColumn[]
  cells: MDTableCell[]
  locks: MDTableLock[]
  canEditStructure: boolean
  canSelectBooth: boolean
  canManageLocks: boolean
  canDelete: boolean
  canEditBooth: (booth: string) => boolean
}>()
const emit = defineEmits<{ refresh: []; error: [message: string] }>()

const localRows = ref<MDTableRow[]>([])
const localColumns = ref<MDTableColumn[]>([])
const values = ref<Record<string, string>>({})
const popupRowId = ref<number | null>(null)
const timers = new Map<string, ReturnType<typeof setTimeout>>()
const columnTimers = new Map<number, ReturnType<typeof setTimeout>>()
const rowTimers = new Map<number, ReturnType<typeof setTimeout>>()
const pending = new Set<string>()
const composing = new Set<string>()

const boothGroups = {
  first: ['CSL', 'VIP(ブルー)', 'VIP(レッド)', 'その他'],
  second: ['2-1', '2-2', '2-3', '2-4', '2-5', '2-6', '2-7', '2-8'],
  third: ['3-1', '3-3', '3-5', '3-7', '3-9', '3-11(スイートラウンジ)'],
}

const boothLocked = computed(() => props.locks.some((lock) => lock.column_key === 'booth' && lock.is_locked))
const sortedRows = computed(() => [...localRows.value].sort((a, b) => a.sort_order - b.sort_order))
const sortedColumns = computed(() => [...localColumns.value].sort((a, b) => a.sort_order - b.sort_order))

watch(() => props.rows, (rows) => {
  localRows.value = rows.map((incoming) => {
    const current = localRows.value.find((row) => row.id === incoming.id)
    return current && rowTimers.has(incoming.id) ? { ...incoming, custom_booth: current.custom_booth } : { ...incoming }
  })
}, { immediate: true, deep: true })
watch(() => props.columns, (columns) => {
  localColumns.value = columns.map((incoming) => {
    const current = localColumns.value.find((column) => column.id === incoming.id)
    return current && columnTimers.has(incoming.id) ? { ...incoming, title: current.title } : { ...incoming }
  })
}, { immediate: true, deep: true })
watch(() => props.cells, (cells) => {
  for (const cell of cells) {
    const key = `${cell.row_id}:${cell.column_id}`
    if (!pending.has(key)) values.value[key] = cell.value
  }
}, { immediate: true, deep: true })

function key(rowId: number, columnId: number) { return `${rowId}:${columnId}` }
function displayBooth(row: MDTableRow) { return row.booth === 'その他' ? row.custom_booth || 'その他' : row.booth || 'ブース' }
function rowEditable(row: MDTableRow) { return props.canEditBooth(row.booth) }

async function saveCell(rowId: number, columnId: number) {
  const cellKey = key(rowId, columnId)
  const scheduled = timers.get(cellKey)
  if (scheduled) clearTimeout(scheduled)
  timers.delete(cellKey)
  const existing = props.cells.find((cell) => cell.row_id === rowId && cell.column_id === columnId)
  try {
    if (existing) await boardService.update('meal-drink', 'md-cells', existing.id, { value: values.value[cellKey] ?? '' })
    else await boardService.create('meal-drink', 'md-cells', { row_id: rowId, column_id: columnId, value: values.value[cellKey] ?? '' })
    pending.delete(cellKey)
    emit('refresh')
  } catch { emit('error', '食数を保存できませんでした。') }
  if (pending.has(cellKey) && !timers.has(cellKey)) timers.set(cellKey, setTimeout(() => void saveCell(rowId, columnId), 2000))
}

function scheduleCell(rowId: number, columnId: number) {
  const cellKey = key(rowId, columnId)
  if (composing.has(cellKey)) return
  pending.add(cellKey)
  const timer = timers.get(cellKey)
  if (timer) clearTimeout(timer)
  timers.set(cellKey, setTimeout(() => void saveCell(rowId, columnId), 450))
}

async function saveRow(row: MDTableRow, fields: Record<string, unknown>) {
  try { await boardService.update('meal-drink', 'md-rows', row.id, fields); emit('refresh') }
  catch { emit('error', '売店名を保存できませんでした。') }
}

async function saveCustomBooth(row: MDTableRow) {
  const scheduled = rowTimers.get(row.id)
  if (scheduled) clearTimeout(scheduled)
  rowTimers.delete(row.id)
  try { await boardService.update('meal-drink', 'md-rows', row.id, { custom_booth: row.custom_booth }); emit('refresh') }
  catch {
    emit('error', 'その他売店名を保存できませんでした。再接続後に自動で再試行します。')
    rowTimers.set(row.id, setTimeout(() => void saveCustomBooth(row), 2000))
  }
}
function scheduleCustomBooth(row: MDTableRow) {
  if (composing.has(`row:${row.id}`)) return
  const old = rowTimers.get(row.id)
  if (old) clearTimeout(old)
  rowTimers.set(row.id, setTimeout(() => void saveCustomBooth(row), 450))
}

function selectBooth(row: MDTableRow, booth: string) {
  row.booth = booth
  if (booth !== 'その他') {
    row.custom_booth = ''
    popupRowId.value = null
  }
  void saveRow(row, { booth, custom_booth: row.custom_booth })
}

async function addRow() {
  try {
    await boardService.create('meal-drink', 'md-rows', { floor_group: props.floorGroup, booth_type: props.floorGroup, booth: '', custom_booth: '', sort_order: localRows.value.length })
    emit('refresh')
  } catch { emit('error', '行を追加できませんでした。') }
}

async function addColumn() {
  try {
    await boardService.create('meal-drink', 'md-columns', { floor_group: props.floorGroup, title: `商品名${localColumns.value.length + 1}`, sort_order: localColumns.value.length })
    emit('refresh')
  } catch { emit('error', '列を追加できませんでした。') }
}

async function saveColumn(column: MDTableColumn) {
  const scheduled = columnTimers.get(column.id)
  if (scheduled) clearTimeout(scheduled)
  columnTimers.delete(column.id)
  try { await boardService.update('meal-drink', 'md-columns', column.id, { title: column.title }); emit('refresh') }
  catch {
    emit('error', '列名を保存できませんでした。再接続後に自動で再試行します。')
    columnTimers.set(column.id, setTimeout(() => void saveColumn(column), 2000))
  }
}
function scheduleColumn(column: MDTableColumn) {
  if (composing.has(`column:${column.id}`)) return
  const old = columnTimers.get(column.id)
  if (old) clearTimeout(old)
  columnTimers.set(column.id, setTimeout(() => void saveColumn(column), 450))
}

async function remove(resource: 'md-rows' | 'md-columns', id: number, label: string) {
  if (!confirm(`この${label}を削除しますか？`)) return
  try { await boardService.remove('meal-drink', resource, id); emit('refresh') }
  catch { emit('error', `${label}を削除できませんでした。`) }
}

async function toggleLock() {
  try { await boardService.lock('meal-drink', { floor_group: props.floorGroup, column_key: 'booth', is_locked: !boothLocked.value }); emit('refresh') }
  catch { emit('error', '売店列のロックを変更できませんでした。') }
}

async function clearData() {
  if (!confirm('書き込まれている食数を一斉クリアしますか？')) return
  try { await boardService.clear('meal-drink', { floor_group: props.floorGroup }); emit('refresh') }
  catch { emit('error', '食数をクリアできませんでした。') }
}

function flush() {
  for (const [cellKey, timer] of timers) {
    clearTimeout(timer)
    const [rowId, columnId] = cellKey.split(':').map(Number)
    void saveCell(rowId!, columnId!)
  }
  for (const [columnId, timer] of columnTimers) {
    clearTimeout(timer)
    const column = localColumns.value.find((item) => item.id === columnId)
    if (column) void saveColumn(column)
  }
  for (const [rowId, timer] of rowTimers) {
    clearTimeout(timer)
    const row = localRows.value.find((item) => item.id === rowId)
    if (row) void saveCustomBooth(row)
  }
}
onBeforeUnmount(flush)
</script>

<template>
  <div class="md-table">
    <div class="header"><h3>{{ title }}</h3><button v-if="canDelete" class="clear" @click="clearData">クリア</button></div>
    <div v-if="canEditStructure" class="toolbar"><button @click="addRow">＋行追加</button><button @click="addColumn">＋列追加</button></div>
    <div class="table-wrap"><table>
      <thead><tr>
        <th class="booth-head">売店 <button class="lock" :disabled="!canManageLocks" @click="toggleLock">{{ boothLocked ? '🔒' : '🔓' }}</button></th>
        <th v-for="column in sortedColumns" :key="column.id">
          <input v-model="column.title" :disabled="!canEditStructure" @input="scheduleColumn(column)" @blur="saveColumn(column)" @compositionstart="composing.add(`column:${column.id}`)" @compositionend="composing.delete(`column:${column.id}`);scheduleColumn(column)" />
          <button v-if="canDelete" class="small-delete" @click="remove('md-columns', column.id, '列')">×</button>
        </th><th v-if="canDelete"></th>
      </tr></thead>
      <tbody><tr v-for="row in sortedRows" :key="row.id">
        <td class="booth-cell">
          <button class="booth" :disabled="boothLocked || !canSelectBooth" @click="popupRowId = popupRowId === row.id ? null : row.id">{{ displayBooth(row) }} ▾</button>
          <div v-if="popupRowId === row.id" class="booth-popup">
            <button v-for="booth in boothGroups[floorGroup]" :key="booth" :disabled="!canEditBooth(booth)" @click="selectBooth(row, booth)">{{ booth }}</button>
            <div v-if="row.booth === 'その他'" class="custom"><input v-model="row.custom_booth" placeholder="売店名" @input="scheduleCustomBooth(row)" @blur="saveCustomBooth(row)" @compositionstart="composing.add(`row:${row.id}`)" @compositionend="composing.delete(`row:${row.id}`);scheduleCustomBooth(row)" /><button @click="popupRowId = null">決定</button></div>
          </div>
        </td>
        <td v-for="column in sortedColumns" :key="column.id">
          <input v-model="values[key(row.id,column.id)]" inputmode="numeric" :disabled="!rowEditable(row)" @input="scheduleCell(row.id,column.id)" @blur="saveCell(row.id,column.id)" @compositionstart="composing.add(key(row.id,column.id))" @compositionend="composing.delete(key(row.id,column.id));scheduleCell(row.id,column.id)" />
        </td>
        <td v-if="canDelete"><button class="small-delete" @click="remove('md-rows', row.id, '行')">削除</button></td>
      </tr></tbody>
    </table></div>
  </div>
</template>

<style scoped>
.md-table{position:relative}.header,.toolbar{display:flex;align-items:center;justify-content:space-between;gap:10px}.header h3{font-size:21px}.toolbar{justify-content:flex-start;margin-bottom:12px}.toolbar button{border:0;border-radius:8px;background:#2563eb;color:#fff;padding:9px 14px;font-weight:700}.clear,.small-delete{border:0;border-radius:7px;background:#fee2e2;color:#b91c1c;padding:8px}.table-wrap{overflow:auto}table{width:100%;min-width:700px;border-collapse:collapse}th,td{position:relative;border:1px solid #dbe4ee;padding:8px;text-align:center}th{background:#f8fafc}th input,td>input{box-sizing:border-box;width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:8px}.booth-head,.booth-cell{min-width:190px}.booth{width:100%;border:0;border-radius:7px;background:#e0f2fe;padding:9px;font-weight:700}.lock{border:0;background:transparent}.booth-popup{position:absolute;top:48px;left:8px;z-index:50;display:grid;width:220px;padding:8px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;box-shadow:0 12px 28px #0f172a26}.booth-popup>button{border:0;background:white;padding:9px;text-align:left}.custom{display:flex;gap:5px}.custom input{min-width:0}.small-delete{margin-top:5px}button:disabled,input:disabled{opacity:.55;cursor:not-allowed}
</style>
