<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { mastersService, reportService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { InventoryCheck, Product, Store } from '@/lib/types'

type SaveState = 'idle' | 'pending' | 'saving' | 'saved' | 'error'

const auth = useAuthStore()
const stores = ref<Store[]>([])
const products = ref<Product[]>([])
const checks = ref<InventoryCheck[]>([])
const checkDate = ref(new Date().toISOString().slice(0, 10))
const storeId = ref<number | ''>('')
const productId = ref<number | ''>('')
const expectedQuantity = ref('')
const actualQuantity = ref('')
const isConfirmed = ref(false)
const note = ref('')
const noteComposing = ref(false)
const loading = ref(false)
const saveState = ref<SaveState>('idle')
const errorMessage = ref('')
let saveTimer: ReturnType<typeof setTimeout> | null = null

const editableStores = computed(() => stores.value.filter(
  (store) => store.is_active && auth.canEditStore(store.id),
))

async function loadChecks(silent = false) {
  if (!silent) loading.value = true
  try {
    checks.value = await reportService.inventoryChecks()
  } catch {
    errorMessage.value = '棚卸情報を取得できませんでした'
  } finally {
    if (!silent) loading.value = false
  }
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [storeData, productData, checkData] = await Promise.all([
      mastersService.stores(),
      mastersService.products('inventory'),
      reportService.inventoryChecks(),
    ])
    stores.value = storeData
    products.value = productData.filter((product) => product.is_active)
    checks.value = checkData
  } catch {
    errorMessage.value = '棚卸情報を取得できませんでした'
  } finally {
    loading.value = false
  }
}

function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer)
  if (
    !auth.canEditReports ||
    noteComposing.value ||
    storeId.value === '' ||
    productId.value === '' ||
    actualQuantity.value === ''
  ) {
    saveState.value = 'idle'
    return
  }
  saveState.value = 'pending'
  saveTimer = setTimeout(() => {
    saveTimer = null
    void saveDraft()
  }, 700)
}

async function saveDraft() {
  if (storeId.value === '' || productId.value === '' || actualQuantity.value === '') return
  const actual = Number(actualQuantity.value)
  const expected = expectedQuantity.value === '' ? null : Number(expectedQuantity.value)
  if (!Number.isInteger(actual) || actual < 0 || (expected !== null && (!Number.isInteger(expected) || expected < 0))) {
    saveState.value = 'error'
    errorMessage.value = '数量には0以上の整数を入力してください'
    return
  }

  saveState.value = 'saving'
  errorMessage.value = ''
  try {
    const saved = await reportService.createInventoryCheck({
      check_date: checkDate.value,
      store_id: Number(storeId.value),
      product_id: Number(productId.value),
      expected_quantity: expected,
      actual_quantity: actual,
      is_confirmed: isConfirmed.value,
      note: note.value || null,
    })
    checks.value = [saved, ...checks.value.filter((check) => check.id !== saved.id)]
    productId.value = ''
    expectedQuantity.value = ''
    actualQuantity.value = ''
    isConfirmed.value = false
    note.value = ''
    saveState.value = 'saved'
  } catch {
    saveState.value = 'error'
    errorMessage.value = '棚卸結果を自動保存できませんでした。入力内容は画面に残っています。'
  }
}

function saveStateLabel() {
  if (saveState.value === 'pending') return '入力内容を保存待ちです'
  if (saveState.value === 'saving') return '保存中…'
  if (saveState.value === 'saved') return '保存済み'
  if (saveState.value === 'error') return '保存に失敗しました'
  return '実数量を入力すると自動保存されます'
}

const { realtimeState } = useRealtimeRefresh('inventory_checks', () => loadChecks(true))

watch(
  [checkDate, storeId, productId, expectedQuantity, actualQuantity, isConfirmed, note],
  scheduleSave,
)

onMounted(load)

onUnmounted(() => {
  if (saveTimer) {
    clearTimeout(saveTimer)
    void saveDraft()
  }
})
</script>

<template>
  <div class="layout">
    <Sidebar />
    <main class="content">
      <AppHeader title="棚卸" description="実数量を入力すると自動保存し、他の端末へ同期します。" />

      <div class="connection-row">
        <span class="realtime-state" :class="realtimeState">
          {{ realtimeState === 'connected' ? '● リアルタイム接続中' : '○ 再接続中' }}
        </span>
      </div>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <section class="panel">
        <div class="form-grid">
          <label>
            日付
            <input
              v-model="checkDate"
              type="date"
              :disabled="!auth.canEditReports || saveState === 'saving'"
            />
          </label>
          <label>
            場所
            <select
              v-model.number="storeId"
              :disabled="!auth.canEditReports || saveState === 'saving'"
            >
              <option value="" disabled>選択してください</option>
              <option v-for="store in editableStores" :key="store.id" :value="store.id">{{ store.name }}</option>
            </select>
          </label>
          <label>
            商品
            <select
              v-model.number="productId"
              :disabled="!auth.canEditReports || saveState === 'saving'"
            >
              <option value="" disabled>選択してください</option>
              <option v-for="product in products" :key="product.id" :value="product.id">
                {{ product.name }} / {{ product.unit }}
              </option>
            </select>
          </label>
          <label>
            期待数量
            <input
              v-model="expectedQuantity"
              type="number"
              min="0"
              placeholder="未入力なら現在在庫"
              :disabled="!auth.canEditReports || saveState === 'saving'"
            />
          </label>
          <label class="wide">
            メモ
            <input
              v-model="note"
              type="text"
              placeholder="任意"
              :disabled="!auth.canEditReports || saveState === 'saving'"
              @compositionstart="noteComposing = true"
              @compositionend="noteComposing = false; scheduleSave()"
            />
          </label>
          <label class="checkbox">
            <input
              v-model="isConfirmed"
              type="checkbox"
              :disabled="!auth.canEditReports || saveState === 'saving'"
            />
            在庫へ反映する
          </label>
          <label>
            実数量
            <input
              v-model="actualQuantity"
              type="number"
              min="0"
              placeholder="最後に入力"
              :disabled="!auth.canEditReports || saveState === 'saving'"
            />
          </label>
        </div>
        <p class="save-message" :class="saveState">{{ saveStateLabel() }}</p>
      </section>

      <section class="panel table-panel">
        <h2>棚卸一覧</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>日付</th>
                <th>場所</th>
                <th>商品</th>
                <th>期待</th>
                <th>実数</th>
                <th>差異</th>
                <th>反映</th>
                <th>メモ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="check in checks" :key="check.id">
                <td>{{ check.check_date }}</td>
                <td>{{ check.store?.name || '-' }}</td>
                <td>{{ check.product?.name || '-' }}</td>
                <td>{{ check.expected_quantity }}{{ check.product?.unit || '' }}</td>
                <td>{{ check.actual_quantity }}{{ check.product?.unit || '' }}</td>
                <td :class="{ negative: (check.difference ?? 0) < 0, positive: (check.difference ?? 0) > 0 }">
                  {{ check.difference ?? check.actual_quantity - check.expected_quantity }}
                </td>
                <td>{{ check.is_confirmed ? '済' : '未反映' }}</td>
                <td>{{ check.note || '-' }}</td>
              </tr>
              <tr v-if="checks.length === 0">
                <td colspan="8" class="empty">棚卸結果はまだありません</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.content {
  flex: 1;
  min-width: 0;
  padding: 40px;
}

.connection-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.realtime-state {
  color: #b45309;
  font-size: 13px;
  font-weight: 700;
}

.realtime-state.connected {
  color: #15803d;
}

.panel {
  margin-bottom: 24px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: white;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(140px, 1fr));
  gap: 14px;
  align-items: end;
}

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: 700;
}

input,
select {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
}

.checkbox {
  min-height: 42px;
  align-items: center;
  flex-direction: row;
}

.wide {
  grid-column: span 2;
}

.save-message {
  margin: 14px 0 0;
  color: #64748b;
  font-size: 13px;
}

.save-message.saved {
  color: #15803d;
}

.save-message.error {
  color: #dc2626;
  font-weight: 700;
}

.table-panel h2 {
  margin-top: 0;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 820px;
  border-collapse: collapse;
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid #eef2f7;
  text-align: left;
}

.negative {
  color: #dc2626;
  font-weight: 800;
}

.positive {
  color: #16a34a;
  font-weight: 800;
}

.empty,
.muted {
  color: #64748b;
}

.error {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fee2e2;
  color: #b91c1c;
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .content {
    padding: 20px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .wide {
    grid-column: auto;
  }
}
</style>
