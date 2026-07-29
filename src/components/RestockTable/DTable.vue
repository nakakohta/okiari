<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { reportService } from '@/lib/services'
import type { Product, RestockReport, RestockStatus, Store } from '@/lib/types'

type SaveState = 'idle' | 'pending' | 'saving' | 'saved' | 'error'
type RestockPatch = { quantity?: number; status?: RestockStatus; note?: string | null }

const props = withDefaults(
  defineProps<{
    title?: string
    store: Store
    products: Product[]
    reports: RestockReport[]
    readonly?: boolean
  }>(),
  {
    title: 'ドリンク補充',
    readonly: false,
  },
)

const emit = defineEmits<{
  saved: [report: RestockReport]
  error: [message: string]
}>()

const statusLabels: Record<RestockStatus, string> = {
  requested: '未補充',
  working: '対応中',
  completed: '完了',
  cancelled: '在庫なし・取消',
}

const prepareMode = ref(false)
const rowValues = reactive<
  Record<number, { quantity: string; note: string; status: RestockStatus }>
>({})
const rowStates = reactive<Record<number, SaveState>>({})
const dirtyRows = new Set<number>()
const updateTimers = new Map<number, ReturnType<typeof setTimeout>>()
const pendingUpdates = new Map<number, RestockPatch>()
const updateVersions = new Map<number, number>()

const draftProductId = ref<number | ''>('')
const draftQuantity = ref('')
const draftNote = ref('')
const draftState = ref<SaveState>('idle')
let draftTimer: ReturnType<typeof setTimeout> | null = null

const filteredReports = computed(() => {
  if (!prepareMode.value) return props.reports
  return props.reports.filter((report) => {
    const status = rowValues[report.id]?.status ?? report.status
    return status === 'requested' || status === 'working'
  })
})

watch(
  () => props.reports,
  (reports) => {
    for (const report of reports) {
      if (dirtyRows.has(report.id)) continue
      rowValues[report.id] = {
        quantity: String(report.quantity),
        note: report.note ?? '',
        status: report.status,
      }
      if (!rowStates[report.id] || rowStates[report.id] === 'saved') rowStates[report.id] = 'idle'
    }
  },
  { immediate: true, deep: true },
)

function queueUpdate(report: RestockReport, patch: RestockPatch, immediate = false) {
  if (props.readonly) return
  dirtyRows.add(report.id)
  updateVersions.set(report.id, (updateVersions.get(report.id) ?? 0) + 1)
  pendingUpdates.set(report.id, { ...pendingUpdates.get(report.id), ...patch })
  rowStates[report.id] = immediate ? 'saving' : 'pending'

  const previousTimer = updateTimers.get(report.id)
  if (previousTimer) clearTimeout(previousTimer)
  if (immediate) {
    updateTimers.delete(report.id)
    void saveUpdate(report.id)
    return
  }
  updateTimers.set(
    report.id,
    setTimeout(() => {
      updateTimers.delete(report.id)
      void saveUpdate(report.id)
    }, 450),
  )
}

function updateQuantity(report: RestockReport, event: Event) {
  const value = (event.target as HTMLInputElement).value
  const row = rowValues[report.id]
  if (!row) return
  row.quantity = value
  const quantity = Number(value)
  if (!Number.isInteger(quantity) || quantity <= 0) {
    rowStates[report.id] = 'error'
    return
  }
  queueUpdate(report, { quantity })
}

function updateNote(report: RestockReport, event: Event) {
  const note = (event.target as HTMLInputElement).value
  const row = rowValues[report.id]
  if (!row) return
  row.note = note
  if ((event as InputEvent).isComposing) return
  queueUpdate(report, { note: note || null })
}

function updateStatus(report: RestockReport, event: Event) {
  const status = (event.target as HTMLSelectElement).value as RestockStatus
  const row = rowValues[report.id]
  if (!row) return
  row.status = status
  queueUpdate(report, { status }, true)
}

async function saveUpdate(reportId: number) {
  const patch = pendingUpdates.get(reportId)
  if (!patch || props.readonly) return
  const savingVersion = updateVersions.get(reportId) ?? 0
  pendingUpdates.delete(reportId)
  rowStates[reportId] = 'saving'
  try {
    const saved = await reportService.updateDrinkRefill(reportId, patch)
    if ((updateVersions.get(reportId) ?? 0) === savingVersion && !pendingUpdates.has(reportId)) {
      dirtyRows.delete(reportId)
      rowValues[reportId] = {
        quantity: String(saved.quantity),
        note: saved.note ?? '',
        status: saved.status,
      }
      rowStates[reportId] = 'saved'
    } else {
      rowStates[reportId] = 'pending'
    }
    emit('saved', saved)
  } catch {
    pendingUpdates.set(reportId, { ...patch, ...pendingUpdates.get(reportId) })
    if ((updateVersions.get(reportId) ?? 0) === savingVersion) {
      rowStates[reportId] = 'error'
      emit('error', '補充依頼を自動保存できませんでした。入力内容は画面に残っています。')
    }
  }
}

function scheduleDraftSave(event?: Event) {
  if (props.readonly) return
  if (event && (event as InputEvent).isComposing) return
  if (draftTimer) clearTimeout(draftTimer)
  if (draftProductId.value === '' || draftQuantity.value === '') {
    draftState.value = 'idle'
    return
  }
  draftState.value = 'pending'
  draftTimer = setTimeout(() => {
    draftTimer = null
    void saveDraft()
  }, 650)
}

async function saveDraft() {
  if (draftProductId.value === '' || props.readonly) return
  const quantity = Number(draftQuantity.value)
  if (!Number.isInteger(quantity) || quantity <= 0) {
    draftState.value = 'error'
    emit('error', '補充数には1以上の整数を入力してください')
    return
  }

  draftState.value = 'saving'
  try {
    const saved = await reportService.createDrinkRefill({
      store_id: props.store.id,
      product_id: Number(draftProductId.value),
      quantity,
      note: draftNote.value || null,
    })
    draftProductId.value = ''
    draftQuantity.value = ''
    draftNote.value = ''
    draftState.value = 'saved'
    emit('saved', saved)
  } catch {
    draftState.value = 'error'
    emit('error', '新しい補充依頼を自動保存できませんでした')
  }
}

function stateLabel(state: SaveState | undefined) {
  if (state === 'pending') return '保存待ち'
  if (state === 'saving') return '保存中…'
  if (state === 'saved') return '保存済み'
  if (state === 'error') return '保存失敗'
  return ''
}

onUnmounted(() => {
  if (draftTimer) {
    clearTimeout(draftTimer)
    void saveDraft()
  }
  for (const [reportId, timer] of updateTimers) {
    clearTimeout(timer)
    void saveUpdate(reportId)
  }
  updateTimers.clear()
})
</script>

<template>
  <div class="d-table">
    <div class="header">
      <div>
        <h3>{{ title }}</h3>
        <p>商品と補充数を入力すると自動保存されます</p>
      </div>
      <button class="prepare-btn" :class="{ active: prepareMode }" @click="prepareMode = !prepareMode">
        {{ prepareMode ? '未完了のみ' : '全件表示' }}
      </button>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>補充状況</th>
            <th>商品名</th>
            <th>補充数</th>
            <th>備考</th>
            <th>同期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="report in filteredReports" :key="report.id">
            <td>
              <select
                :value="rowValues[report.id]?.status ?? report.status"
                :disabled="readonly"
                :class="rowValues[report.id]?.status ?? report.status"
                @change="updateStatus(report, $event)"
              >
                <option v-for="(label, status) in statusLabels" :key="status" :value="status">
                  {{ label }}
                </option>
              </select>
            </td>
            <td>{{ report.product?.name ?? '不明な商品' }}</td>
            <td>
              <div class="quantity-field">
                <input
                  :value="rowValues[report.id]?.quantity ?? String(report.quantity)"
                  type="number"
                  min="1"
                  step="1"
                  :disabled="readonly"
                  @input="updateQuantity(report, $event)"
                />
                <span>{{ report.product?.unit ?? '' }}</span>
              </div>
            </td>
            <td>
              <input
                :value="rowValues[report.id]?.note ?? report.note ?? ''"
                type="text"
                :disabled="readonly"
                placeholder="任意"
                @input="updateNote(report, $event)"
              />
            </td>
            <td>
              <span class="save-state" :class="rowStates[report.id]">
                {{ stateLabel(rowStates[report.id]) }}
              </span>
            </td>
          </tr>

          <tr v-if="!readonly" class="draft-row">
            <td><span class="new-badge">新規</span></td>
            <td>
              <select
                v-model.number="draftProductId"
                :disabled="draftState === 'saving'"
                @change="scheduleDraftSave"
              >
                <option value="" disabled>商品を選択</option>
                <option v-for="product in products" :key="product.id" :value="product.id">
                  {{ product.name }}
                </option>
              </select>
            </td>
            <td>
              <input
                v-model="draftQuantity"
                type="number"
                min="1"
                step="1"
                placeholder="補充数"
                :disabled="draftState === 'saving'"
                @input="scheduleDraftSave"
              />
            </td>
            <td>
              <input
                v-model="draftNote"
                type="text"
                placeholder="任意"
                :disabled="draftState === 'saving'"
                @input="scheduleDraftSave"
              />
            </td>
            <td>
              <span class="save-state" :class="draftState">{{ stateLabel(draftState) }}</span>
            </td>
          </tr>

          <tr v-if="filteredReports.length === 0 && readonly">
            <td colspan="5" class="empty">補充依頼はありません</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.d-table {
  margin-bottom: 34px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 14px;
}

.header h3,
.header p {
  margin: 0;
}

.header p {
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
}

.prepare-btn {
  border: 0;
  border-radius: 8px;
  background: #e2e8f0;
  color: #334155;
  padding: 9px 14px;
  cursor: pointer;
  font-weight: 700;
}

.prepare-btn.active {
  background: #2563eb;
  color: white;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
}

table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
  background: white;
}

th,
td {
  padding: 10px;
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

th:last-child,
td:last-child {
  border-right: 0;
}

tbody tr:last-child td {
  border-bottom: 0;
}

th {
  background: #f1f5f9;
  color: #334155;
  font-size: 13px;
}

input,
select {
  width: 100%;
  min-width: 110px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  padding: 8px 10px;
  font: inherit;
}

input:focus,
select:focus {
  border-color: #2563eb;
  outline: 3px solid rgba(37, 99, 235, 0.12);
}

input:disabled,
select:disabled {
  background: #f1f5f9;
  color: #64748b;
}

select.requested {
  color: #dc2626;
}

select.working {
  color: #b45309;
}

select.completed {
  color: #15803d;
}

.quantity-field {
  display: flex;
  align-items: center;
  gap: 6px;
}

.quantity-field span {
  color: #64748b;
}

.draft-row {
  background: #eff6ff;
}

.new-badge {
  display: inline-block;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  padding: 4px 9px;
  font-size: 12px;
  font-weight: 800;
}

.save-state {
  color: #64748b;
  font-size: 11px;
  white-space: nowrap;
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
