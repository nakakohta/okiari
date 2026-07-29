<script setup lang="ts">
import { computed, onUnmounted, reactive, watch } from 'vue'
import { reportService } from '@/lib/services'
import type { MealReport, Product, Store } from '@/lib/types'

type CellSaveState = 'idle' | 'pending' | 'saving' | 'saved' | 'error'

const props = withDefaults(
  defineProps<{
    title?: string
    reportDate: string
    stores: Store[]
    products: Product[]
    reports: MealReport[]
    canEditStore: (storeId: number) => boolean
    readonly?: boolean
  }>(),
  {
    title: '',
    readonly: false,
  },
)

const emit = defineEmits<{
  saved: [report: MealReport]
  error: [message: string]
}>()

const cellValues = reactive<Record<string, string>>({})
const saveStates = reactive<Record<string, CellSaveState>>({})
const dirtyKeys = new Set<string>()
const saveTimers = new Map<string, ReturnType<typeof setTimeout>>()
const editVersions = new Map<string, number>()
const pendingCells = new Map<
  string,
  { reportDate: string; storeId: number; productId: number }
>()

const reportMap = computed(() => {
  const map = new Map<string, MealReport>()
  for (const report of props.reports) {
    map.set(`${report.store_id}:${report.product_id}`, report)
  }
  return map
})

function cellKey(reportDate: string, storeId: number, productId: number) {
  return `${reportDate}:${storeId}:${productId}`
}

function reportKey(storeId: number, productId: number) {
  return `${storeId}:${productId}`
}

function syncFromReports() {
  for (const store of props.stores) {
    for (const product of props.products) {
      const key = cellKey(props.reportDate, store.id, product.id)
      if (dirtyKeys.has(key)) continue
      const report = reportMap.value.get(reportKey(store.id, product.id))
      cellValues[key] = report ? String(report.quantity) : ''
      if (!saveStates[key] || saveStates[key] === 'saved') saveStates[key] = 'idle'
    }
  }
}

watch(
  () => [props.reportDate, props.stores, props.products, props.reports],
  syncFromReports,
  { immediate: true, deep: true },
)

function scheduleSave(storeId: number, productId: number, event: Event) {
  const input = event.target as HTMLInputElement
  const reportDate = props.reportDate
  const key = cellKey(reportDate, storeId, productId)
  cellValues[key] = input.value
  dirtyKeys.add(key)
  editVersions.set(key, (editVersions.get(key) ?? 0) + 1)
  saveStates[key] = 'pending'
  pendingCells.set(key, { reportDate, storeId, productId })

  const previousTimer = saveTimers.get(key)
  if (previousTimer) clearTimeout(previousTimer)
  saveTimers.set(
    key,
    setTimeout(() => {
      saveTimers.delete(key)
      void saveCell(key)
    }, 450),
  )
}

async function saveCell(key: string) {
  const pending = pendingCells.get(key)
  if (!pending || props.readonly || !props.canEditStore(pending.storeId)) return
  const rawValue = cellValues[key] ?? ''
  const savingVersion = editVersions.get(key) ?? 0
  const quantity = rawValue === '' ? 0 : Number(rawValue)
  if (!Number.isInteger(quantity) || quantity < 0) {
    saveStates[key] = 'error'
    emit('error', '食数には0以上の整数を入力してください')
    return
  }

  saveStates[key] = 'saving'
  try {
    const saved = await reportService.upsertMealReport({
      report_date: pending.reportDate,
      store_id: pending.storeId,
      product_id: pending.productId,
      quantity,
      note: null,
    })
    if ((editVersions.get(key) ?? 0) === savingVersion) {
      dirtyKeys.delete(key)
      pendingCells.delete(key)
      cellValues[key] = String(saved.quantity)
      saveStates[key] = 'saved'
    } else {
      saveStates[key] = 'pending'
    }
    emit('saved', saved)
  } catch {
    if ((editVersions.get(key) ?? 0) === savingVersion) {
      saveStates[key] = 'error'
      emit('error', '食数を自動保存できませんでした。入力内容は画面に残っています。')
    }
  }
}

function stateLabel(key: string) {
  const state = saveStates[key] ?? 'idle'
  if (state === 'pending') return '保存待ち'
  if (state === 'saving') return '保存中…'
  if (state === 'saved') return '保存済み'
  if (state === 'error') return '保存失敗'
  return ''
}

onUnmounted(() => {
  for (const [key, timer] of saveTimers) {
    clearTimeout(timer)
    void saveCell(key)
  }
  saveTimers.clear()
})
</script>

<template>
  <div class="md-table">
    <div v-if="title" class="table-heading">
      <h3>{{ title }}</h3>
      <span>入力内容は自動保存されます</span>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th class="store-column">売店名</th>
            <th v-for="product in products" :key="product.id">
              {{ product.name }}
              <small>{{ product.unit }}</small>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="store in stores" :key="store.id">
            <th class="store-name">{{ store.name }}</th>
            <td v-for="product in products" :key="product.id">
              <div class="cell-editor">
                <input
                  :value="cellValues[cellKey(reportDate, store.id, product.id)] ?? ''"
                  type="number"
                  min="0"
                  step="1"
                  inputmode="numeric"
                  :disabled="readonly || !canEditStore(store.id)"
                  aria-label="食数"
                  @input="scheduleSave(store.id, product.id, $event)"
                />
                <span
                  class="save-state"
                  :class="saveStates[cellKey(reportDate, store.id, product.id)]"
                >
                  {{ stateLabel(cellKey(reportDate, store.id, product.id)) }}
                </span>
              </div>
            </td>
          </tr>
          <tr v-if="stores.length === 0">
            <td :colspan="products.length + 1" class="empty">表示できる売店がありません</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.md-table {
  min-width: 0;
}

.table-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 14px;
}

.table-heading h3 {
  margin: 0;
}

.table-heading span {
  color: #64748b;
  font-size: 12px;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
}

table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
  background: #fff;
}

th,
td {
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  padding: 10px;
  text-align: center;
}

tr:last-child th,
tr:last-child td {
  border-bottom: 0;
}

th:last-child,
td:last-child {
  border-right: 0;
}

thead th {
  background: #f1f5f9;
  color: #334155;
  font-size: 13px;
}

thead small {
  display: block;
  margin-top: 3px;
  color: #64748b;
  font-weight: 500;
}

.store-column,
.store-name {
  position: sticky;
  left: 0;
  z-index: 1;
  min-width: 150px;
}

.store-name {
  background: #f8fafc;
  text-align: left;
}

.cell-editor {
  display: grid;
  justify-items: center;
  gap: 4px;
  min-width: 110px;
}

input {
  width: 88px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px;
  text-align: right;
  font: inherit;
}

input:focus {
  border-color: #2563eb;
  outline: 3px solid rgba(37, 99, 235, 0.12);
}

input:disabled {
  background: #f1f5f9;
  color: #64748b;
}

.save-state {
  min-height: 16px;
  color: #64748b;
  font-size: 10px;
}

.save-state.saved {
  color: #15803d;
}

.save-state.error {
  color: #dc2626;
  font-weight: 700;
}

.empty {
  color: #64748b;
  text-align: center;
}
</style>
