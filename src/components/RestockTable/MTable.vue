<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { boardService } from '@/lib/services'
import type { MTableRow, Product, Store } from '@/lib/types'

const props = defineProps<{
  rows: MTableRow[]
  stores: Store[]
  products: Product[]
  canEditStore: (storeId: number) => boolean
  canConfirm: boolean
  canDelete: boolean
}>()
const emit = defineEmits<{ refresh: []; error: [message: string] }>()
type Field = 'store_id' | 'product_id' | 'expected_quantity' | 'actual_quantity' | 'note'
const localRows = ref<MTableRow[]>([])
const timers = new Map<string, ReturnType<typeof setTimeout>>()
const pending = new Set<string>()
const composing = new Set<string>()

const sortedRows = computed(() => [...localRows.value].sort((a, b) => a.sort_order - b.sort_order))
watch(() => props.rows, (rows) => {
  localRows.value = rows.map((incoming) => {
    const current = localRows.value.find((row) => row.id === incoming.id)
    if (!current) return { ...incoming }
    const merged = { ...incoming }
    for (const field of ['store_id','product_id','expected_quantity','actual_quantity','note'] as Field[]) {
      if (pending.has(`${incoming.id}:${field}`)) merged[field] = current[field] as never
    }
    return merged
  })
}, { immediate: true, deep: true })

function storeName(id: number) { return props.stores.find((store) => store.id === id)?.name ?? '-' }
function productName(id: number) { return props.products.find((product) => product.id === id)?.name ?? '-' }
function unit(id: number) { return props.products.find((product) => product.id === id)?.unit ?? '' }

async function save(row: MTableRow, field: Field) {
  const timerKey = `${row.id}:${field}`
  const scheduled = timers.get(timerKey)
  if (scheduled) clearTimeout(scheduled)
  timers.delete(timerKey)
  if (field === 'expected_quantity' || field === 'actual_quantity') row[field] = Math.max(0, Number(row[field]) || 0)
  try { await boardService.update('inventory', 'm-rows', row.id, { [field]: row[field] }); pending.delete(timerKey) }
  catch {
    emit('error', '棚卸内容を保存できませんでした。再接続後に自動で再試行します。')
    timers.set(timerKey, setTimeout(() => void save(row, field), 2000))
  }
}
function schedule(row: MTableRow, field: Field) {
  const timerKey = `${row.id}:${field}`
  if (composing.has(timerKey)) return
  pending.add(timerKey)
  const old = timers.get(timerKey)
  if (old) clearTimeout(old)
  timers.set(timerKey, setTimeout(() => void save(row, field), 450))
}
async function addRow() {
  const store = props.stores.find((item) => item.is_active && props.canEditStore(item.id))
  const product = props.products.find((item) => item.is_active)
  if (!store || !product) { emit('error', '追加に必要な売店または商品がありません。'); return }
  try { await boardService.create('inventory', 'm-rows', { store_id: store.id, product_id: product.id, expected_quantity: 0, actual_quantity: 0, note: '', is_confirmed: false, sort_order: localRows.value.length }); emit('refresh') }
  catch { emit('error', '棚卸行を追加できませんでした。') }
}
async function confirmRow(row: MTableRow) {
  try { await boardService.update('inventory', 'm-rows', row.id, { is_confirmed: !row.is_confirmed }); emit('refresh') }
  catch { emit('error', '棚卸を確定できませんでした。') }
}
async function removeRow(row: MTableRow) {
  if (!confirm('この棚卸行を削除しますか？')) return
  try { await boardService.remove('inventory', 'm-rows', row.id); emit('refresh') }
  catch { emit('error', '棚卸行を削除できませんでした。') }
}
async function clearRows() {
  if (!confirm('実数・備考・確認状態をクリアしますか？')) return
  try { await boardService.clear('inventory'); emit('refresh') }
  catch { emit('error', '棚卸表をクリアできませんでした。') }
}
function flush() {
  for (const [timerKey, timer] of timers) {
    clearTimeout(timer)
    const [idText, field] = timerKey.split(':') as [string, Field]
    const row = localRows.value.find((item) => item.id === Number(idText))
    if (row) void save(row, field)
  }
}
onBeforeUnmount(flush)
</script>

<template>
  <div class="m-table">
    <div class="toolbar"><button @click="addRow">＋行追加</button><button v-if="canDelete" class="clear" @click="clearRows">クリア</button></div>
    <div class="table-wrap"><table>
      <thead><tr><th>売店</th><th>商品</th><th>予定数</th><th>実数</th><th>差分</th><th>確認状態</th><th>備考</th><th v-if="canDelete"></th></tr></thead>
      <tbody><tr v-for="row in sortedRows" :key="row.id" :class="{ confirmed: row.is_confirmed }">
        <td><select v-model="row.store_id" :disabled="row.is_confirmed || !canEditStore(row.store_id)" @change="save(row,'store_id')"><option v-for="store in stores.filter(item => item.is_active && canEditStore(item.id))" :key="store.id" :value="store.id">{{ store.name }}</option></select><span class="print">{{ storeName(row.store_id) }}</span></td>
        <td><select v-model="row.product_id" :disabled="row.is_confirmed || !canEditStore(row.store_id)" @change="save(row,'product_id')"><option v-for="product in products.filter(item => item.is_active)" :key="product.id" :value="product.id">{{ product.name }}</option></select><span class="print">{{ productName(row.product_id) }}</span></td>
        <td><div class="quantity"><input v-model.number="row.expected_quantity" type="number" min="0" :disabled="row.is_confirmed || !canEditStore(row.store_id)" @input="schedule(row,'expected_quantity')" @blur="save(row,'expected_quantity')" /><span>{{ unit(row.product_id) }}</span></div></td>
        <td><div class="quantity"><input v-model.number="row.actual_quantity" type="number" min="0" :disabled="row.is_confirmed || !canEditStore(row.store_id)" @input="schedule(row,'actual_quantity')" @blur="save(row,'actual_quantity')" /><span>{{ unit(row.product_id) }}</span></div></td>
        <td :class="{ negative: row.actual_quantity-row.expected_quantity < 0, positive: row.actual_quantity-row.expected_quantity > 0 }">{{ row.actual_quantity - row.expected_quantity }}</td>
        <td><button class="confirm" :class="{ active: row.is_confirmed }" :disabled="!canConfirm" @click="confirmRow(row)">{{ row.is_confirmed ? '確定済み' : '未確定' }}</button></td>
        <td><input v-model="row.note" :disabled="row.is_confirmed || !canEditStore(row.store_id)" @input="schedule(row,'note')" @blur="save(row,'note')" @compositionstart="composing.add(`${row.id}:note`)" @compositionend="composing.delete(`${row.id}:note`);schedule(row,'note')" /></td>
        <td v-if="canDelete"><button class="delete" @click="removeRow(row)">削除</button></td>
      </tr></tbody>
    </table></div>
  </div>
</template>

<style scoped>
.toolbar{display:flex;justify-content:space-between;margin-bottom:12px}.toolbar button{border:0;border-radius:8px;background:#2563eb;color:white;padding:9px 14px;font-weight:700}.toolbar .clear,.delete{background:#fee2e2;color:#b91c1c}.table-wrap{overflow:auto}table{width:100%;min-width:1000px;border-collapse:collapse}th,td{border:1px solid #dbe4ee;padding:9px;text-align:center}th{background:#f8fafc}tr.confirmed{background:#f0fdf4}input,select{box-sizing:border-box;width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:8px}.quantity{display:flex;align-items:center;gap:5px}.quantity span{white-space:nowrap}.confirm{border:0;border-radius:20px;background:#fef3c7;color:#92400e;padding:8px 12px;font-weight:700}.confirm.active{background:#dcfce7;color:#166534}.delete{border:0;border-radius:6px;padding:7px}.negative{color:#dc2626;font-weight:800}.positive{color:#16a34a;font-weight:800}.print{display:none}button:disabled,input:disabled,select:disabled{opacity:.6;cursor:not-allowed}@media print{select{display:none}.print{display:inline}}
</style>
