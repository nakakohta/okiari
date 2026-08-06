<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { boardService } from '@/lib/services'
import type { MFTableContainer, MFTableRow } from '@/lib/types'

const props = defineProps<{
  sectionId: number
  rows: MFTableRow[]
  containers: MFTableContainer[]
  readonly: boolean
  canDelete: boolean
}>()
const emit = defineEmits<{ refresh: []; error: [message: string] }>()

type RowField = 'icon' | 'item_name' | 'subtext' | 'note'
type ContainerField = 'name' | 'quantity'
const localRows = ref<MFTableRow[]>([])
const localContainers = ref<MFTableContainer[]>([])
const openMenu = ref<number | null>(null)
const draggedRow = ref<number | null>(null)
const timers = new Map<string, ReturnType<typeof setTimeout>>()
const composing = new Set<string>()

const sortedRows = computed(() => [...localRows.value].sort((a, b) => a.sort_order - b.sort_order))
function containersFor(rowId: number) { return localContainers.value.filter((item) => item.row_id === rowId).sort((a, b) => a.sort_order - b.sort_order) }

watch(() => props.rows, (rows) => {
  localRows.value = rows.map((incoming) => {
    const current = localRows.value.find((row) => row.id === incoming.id)
    if (!current) return { ...incoming }
    const merged = { ...incoming }
    for (const field of ['icon','item_name','subtext','note'] as RowField[]) {
      if (timers.has(`mf-rows:${incoming.id}:${field}`)) merged[field] = current[field] as never
    }
    return merged
  })
}, { immediate: true, deep: true })
watch(() => props.containers, (containers) => {
  localContainers.value = containers.map((incoming) => {
    const current = localContainers.value.find((item) => item.id === incoming.id)
    if (!current) return { ...incoming }
    const merged = { ...incoming }
    for (const field of ['name','quantity'] as ContainerField[]) {
      if (timers.has(`mf-containers:${incoming.id}:${field}`)) merged[field] = current[field] as never
    }
    return merged
  })
}, { immediate: true, deep: true })

async function save(resource: 'mf-rows' | 'mf-containers', id: number, field: RowField | ContainerField, value: unknown) {
  const timerKey = `${resource}:${id}:${field}`
  const scheduled = timers.get(timerKey)
  if (scheduled) clearTimeout(scheduled)
  timers.delete(timerKey)
  const normalized = field === 'quantity' ? Math.max(0, Number(value) || 0) : value
  try { await boardService.update('meal-food', resource, id, { [field]: normalized }) }
  catch {
    emit('error', '入力内容を保存できませんでした。再接続後に自動で再試行します。')
    timers.set(timerKey, setTimeout(() => void save(resource, id, field, normalized), 2000))
  }
}

function schedule(resource: 'mf-rows' | 'mf-containers', id: number, field: RowField | ContainerField, value: unknown) {
  const timerKey = `${resource}:${id}:${field}`
  if (composing.has(timerKey)) return
  const old = timers.get(timerKey)
  if (old) clearTimeout(old)
  timers.set(timerKey, setTimeout(() => void save(resource, id, field, value), 450))
}

async function addRow() {
  try {
    await boardService.create<MFTableRow>('meal-food', 'mf-rows', { section_id: props.sectionId, icon: '🍚', item_name: '', subtext: '', note: '', sort_order: localRows.value.length })
    emit('refresh')
  } catch { emit('error', '品目を追加できませんでした。') }
}

async function addContainer(row: MFTableRow) {
  try {
    await boardService.create('meal-food', 'mf-containers', { row_id: row.id, name: '', container_type: 'register', quantity: 0, sort_order: containersFor(row.id).length })
    emit('refresh')
  } catch { emit('error', '容器を追加できませんでした。') }
}

async function remove(resource: 'mf-rows' | 'mf-containers', id: number, label: string) {
  if (!confirm(`この${label}を削除しますか？`)) return
  try { await boardService.remove('meal-food', resource, id); emit('refresh') }
  catch { emit('error', `${label}を削除できませんでした。`) }
}

async function selectType(container: MFTableContainer, type: MFTableContainer['container_type']) {
  container.container_type = type
  if (type !== 'register' && container.quantity === 0) container.quantity = 100
  try { await boardService.update('meal-food', 'mf-containers', container.id, { container_type: type, quantity: container.quantity }); openMenu.value = null }
  catch { emit('error', '容器種別を保存できませんでした。') }
}

function typeLabel(type: MFTableContainer['container_type']) {
  if (type === 'insulated_box') return '保温ボックス'
  if (type === 'food_warmer') return 'フードウォーマー'
  return '打込み'
}
function typeEmoji(type: MFTableContainer['container_type']) { return type === 'insulated_box' ? '🧰' : type === 'food_warmer' ? '♨️' : '🔢' }
function levelClass(quantity: number) { return quantity >= 80 ? 'good' : quantity >= 30 ? 'warn' : 'danger' }

async function drop(index: number) {
  if (draggedRow.value === null || draggedRow.value === index) return
  const ordered = sortedRows.value
  const [moved] = ordered.splice(draggedRow.value, 1)
  if (!moved) return
  ordered.splice(index, 0, moved)
  localRows.value = ordered
  draggedRow.value = null
  try { await boardService.reorder('meal-food', 'mf-rows', ordered.map((row) => row.id)) }
  catch { emit('error', '品目の並び順を保存できませんでした。') }
}

function flush() {
  for (const [timerKey, timer] of timers) {
    clearTimeout(timer)
    const [resource, idText, field] = timerKey.split(':') as ['mf-rows' | 'mf-containers', string, RowField | ContainerField]
    const item = resource === 'mf-rows' ? localRows.value.find((row) => row.id === Number(idText)) : localContainers.value.find((row) => row.id === Number(idText))
    if (item) void save(resource, Number(idText), field, (item as unknown as Record<string, unknown>)[field])
  }
}
onBeforeUnmount(flush)
</script>

<template>
  <div class="mf-table" @click="openMenu = null">
    <p class="desc">品目ごとに保温ボックス・フードウォーマーの割合、または打込み数を登録できます。</p>
    <div class="table-wrap"><table>
      <thead><tr><th class="item-col">品目</th><th>容器・フードウォーマー</th><th class="note-col">備考</th></tr></thead>
      <tbody><tr v-for="(row,index) in sortedRows" :key="row.id" draggable="true" @dragstart="draggedRow = index" @dragover.prevent @drop="drop(index)">
        <td class="item-cell">
          <div class="item-head"><span class="grip">⠿</span><input v-model="row.icon" class="icon" :disabled="readonly" @input="schedule('mf-rows',row.id,'icon',row.icon)" /><div class="meta">
            <input v-model="row.item_name" class="name" placeholder="品目名" :disabled="readonly" @input="schedule('mf-rows',row.id,'item_name',row.item_name)" @blur="save('mf-rows',row.id,'item_name',row.item_name)" @compositionstart="composing.add(`mf-rows:${row.id}:item_name`)" @compositionend="composing.delete(`mf-rows:${row.id}:item_name`);schedule('mf-rows',row.id,'item_name',row.item_name)" />
            <input v-model="row.subtext" placeholder="サブテキスト" :disabled="readonly" @input="schedule('mf-rows',row.id,'subtext',row.subtext)" @blur="save('mf-rows',row.id,'subtext',row.subtext)" @compositionstart="composing.add(`mf-rows:${row.id}:subtext`)" @compositionend="composing.delete(`mf-rows:${row.id}:subtext`);schedule('mf-rows',row.id,'subtext',row.subtext)" />
          </div></div>
          <button v-if="canDelete" class="remove" @click="remove('mf-rows',row.id,'品目')">削除</button>
        </td>
        <td><div class="containers">
          <div v-for="container in containersFor(row.id)" :key="container.id" class="card">
            <div class="type-row"><button class="type" :disabled="readonly" @click.stop="openMenu = openMenu === container.id ? null : container.id">{{ typeEmoji(container.container_type) }} {{ typeLabel(container.container_type) }} ▾</button><button v-if="canDelete" class="x" @click="remove('mf-containers',container.id,'容器')">×</button></div>
            <div v-if="openMenu === container.id" class="menu" @click.stop><button @click="selectType(container,'insulated_box')">🧰 保温ボックス</button><button @click="selectType(container,'food_warmer')">♨️ フードウォーマー</button><button @click="selectType(container,'register')">🔢 打込み</button></div>
            <input v-model="container.name" placeholder="名称" :disabled="readonly" @input="schedule('mf-containers',container.id,'name',container.name)" @blur="save('mf-containers',container.id,'name',container.name)" @compositionstart="composing.add(`mf-containers:${container.id}:name`)" @compositionend="composing.delete(`mf-containers:${container.id}:name`);schedule('mf-containers',container.id,'name',container.name)" />
            <div v-if="container.container_type === 'register'" class="number"><input v-model.number="container.quantity" type="number" min="0" :disabled="readonly" @input="schedule('mf-containers',container.id,'quantity',container.quantity)" @blur="save('mf-containers',container.id,'quantity',container.quantity)" /><span>個</span></div>
            <div v-else class="battery-wrap"><div class="battery" :class="levelClass(container.quantity)"><div class="battery-terminal"></div><div class="battery-fill" :style="{width:`${Math.min(100,container.quantity)}%`}"></div><div class="battery-content"><b>{{ Math.round(container.quantity / 10) }}割</b></div></div><input v-model.number="container.quantity" class="range" type="range" min="0" max="100" :disabled="readonly" @input="schedule('mf-containers',container.id,'quantity',container.quantity)" @change="save('mf-containers',container.id,'quantity',container.quantity)" /></div>
          </div><button class="add-container-card" :disabled="readonly" @click="addContainer(row)"><span>＋</span><span>追加</span></button>
        </div></td>
        <td><textarea v-model="row.note" :disabled="readonly" @input="schedule('mf-rows',row.id,'note',row.note)" @blur="save('mf-rows',row.id,'note',row.note)" @compositionstart="composing.add(`mf-rows:${row.id}:note`)" @compositionend="composing.delete(`mf-rows:${row.id}:note`);schedule('mf-rows',row.id,'note',row.note)"></textarea></td>
      </tr></tbody><tfoot><tr><td colspan="3" class="add-row-cell"><button class="add-row" :disabled="readonly" @click="addRow">＋ 品目を追加</button></td></tr></tfoot>
    </table></div>
  </div>
</template>

<style scoped>
.desc{color:#64748b}.table-wrap{overflow:auto}table{width:100%;min-width:900px;border-collapse:collapse}th,td{vertical-align:top;border:1px solid #dbe4ee;padding:12px}th{background:#f8fafc}.item-col{width:260px}.note-col{width:200px}.item-head,.type-row,.number{display:flex;align-items:center;gap:8px}.grip{color:#94a3b8;cursor:grab}.icon{width:42px}.meta{display:grid;flex:1;gap:6px}.name{font-weight:700}.containers{display:flex;gap:12px;overflow-x:auto;padding-bottom:4px}.card,.add-container-card{flex:0 0 220px;min-width:220px}.card{position:relative;padding:12px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}.type{flex:1;border:0;border-radius:7px;background:#eff6ff;padding:8px;text-align:left}.menu{position:absolute;z-index:20;display:grid;width:220px;padding:7px;border:1px solid #cbd5e1;border-radius:8px;background:white;box-shadow:0 8px 20px #0002}.menu button{border:0;background:white;padding:8px;text-align:left}input,textarea{box-sizing:border-box;width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:8px}textarea{min-height:130px}.battery-wrap{margin-top:10px}.battery{position:relative;height:72px;margin:0 8px 10px 0;overflow:visible;border:3px solid #334155;border-radius:8px;background:#fff}.battery-terminal{position:absolute;top:24px;right:-10px;width:8px;height:24px;border-radius:0 4px 4px 0;background:#334155}.battery-fill{position:absolute;inset:0 auto 0 0;max-width:100%;background:linear-gradient(90deg,#bbf7d0,#4ade80);transition:width .2s}.battery.warn .battery-fill{background:linear-gradient(90deg,#fef3c7,#f59e0b)}.battery.danger .battery-fill{background:linear-gradient(90deg,#fee2e2,#ef4444)}.battery-content{position:absolute;inset:0;display:grid;place-items:center;font-size:17px}.range{width:100%;accent-color:#2563eb}.remove,.x{border:0;background:#fee2e2;color:#b91c1c}.remove{margin-top:10px;padding:7px;border-radius:6px}.add-container-card{display:grid;place-items:center;border:2px dashed #93c5fd;border-radius:12px;background:#eff6ff;color:#2563eb;font-weight:800;cursor:pointer}.add-container-card span:first-child{font-size:28px}.add-row-cell{background:#fff}.add-row{width:100%;border:2px dashed #3b82f6;border-radius:9px;background:#eff6ff;color:#2563eb;padding:12px;font-weight:800}button:disabled,input:disabled,textarea:disabled{opacity:.55;cursor:not-allowed}
</style>
