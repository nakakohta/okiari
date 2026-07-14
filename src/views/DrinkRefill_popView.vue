<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { mastersService, reportService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { Product, RestockReport, RestockStatus, Store } from '@/lib/types'

const statusLabels: Record<RestockStatus, string> = {
  requested: '依頼',
  working: '対応中',
  completed: '完了',
  cancelled: '取消',
}

const auth = useAuthStore()
const stores = ref<Store[]>([])
const products = ref<Product[]>([])
const reports = ref<RestockReport[]>([])
const storeId = ref<number | ''>('')
const productId = ref<number | ''>('')
const quantity = ref(1)
const note = ref('')
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [storeData, productData, reportData] = await Promise.all([
      mastersService.stores(),
      mastersService.products('drink'),
      reportService.drinkRefills(),
    ])
    stores.value = storeData
    products.value = productData
    reports.value = reportData
  } catch {
    errorMessage.value = 'ドリンク補充情報を取得できませんでした'
  } finally {
    loading.value = false
  }
}

async function save() {
  if (storeId.value === '' || productId.value === '') {
    errorMessage.value = '場所と商品を選択してください'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    await reportService.createDrinkRefill({
      store_id: Number(storeId.value),
      product_id: Number(productId.value),
      quantity: quantity.value,
      note: note.value || null,
    })
    quantity.value = 1
    note.value = ''
    await load()
  } catch {
    errorMessage.value = 'ドリンク補充依頼を保存できませんでした'
  } finally {
    saving.value = false
  }
}

async function updateStatus(report: RestockReport, status: RestockStatus) {
  errorMessage.value = ''
  try {
    const updated = await reportService.updateDrinkStatus(report.id, status)
    reports.value = reports.value.map((item) => (item.id === report.id ? updated : item))
  } catch {
    errorMessage.value = 'ステータスを更新できませんでした'
  }
}

onMounted(load)
</script>

<template>
  <div class="layout">
    <Sidebar />
    <main class="content">
      <AppHeader title="ドリンク補充" description="ドリンク補充依頼を登録し、対応状況を管理します。" />
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <form class="panel form-grid" @submit.prevent="save">
        <label>
          場所
          <select v-model.number="storeId" required>
            <option value="" disabled>選択してください</option>
            <option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}</option>
          </select>
        </label>
        <label>
          商品
          <select v-model.number="productId" required>
            <option value="" disabled>選択してください</option>
            <option v-for="product in products" :key="product.id" :value="product.id">
              {{ product.name }} / {{ product.unit }}
            </option>
          </select>
        </label>
        <label>
          数量
          <input v-model.number="quantity" type="number" min="1" required />
        </label>
        <label class="wide">
          メモ
          <input v-model="note" type="text" placeholder="任意" />
        </label>
        <button type="submit" :disabled="saving || !auth.canEditReports">
          {{ auth.canEditReports ? (saving ? '保存中...' : '依頼する') : '閲覧のみ' }}
        </button>
      </form>

      <section class="panel">
        <h2>補充依頼一覧</h2>
        <table>
          <thead>
            <tr>
              <th>依頼日時</th>
              <th>場所</th>
              <th>商品</th>
              <th>数量</th>
              <th>状態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="report in reports" :key="report.id">
              <td>{{ new Date(report.requested_at).toLocaleString() }}</td>
              <td>{{ report.store?.name || '-' }}</td>
              <td>{{ report.product?.name || '-' }}</td>
              <td>{{ report.quantity }}{{ report.product?.unit || '' }}</td>
              <td>
                <span class="status" :class="report.status">{{ statusLabels[report.status] }}</span>
              </td>
              <td class="actions">
                <button
                  v-for="status in Object.keys(statusLabels) as RestockStatus[]"
                  :key="status"
                  type="button"
                  class="secondary"
                  :disabled="!auth.canEditReports || report.status === status"
                  @click="updateStatus(report, status)"
                >
                  {{ statusLabels[status] }}
                </button>
              </td>
            </tr>
            <tr v-if="reports.length === 0">
              <td colspan="6" class="empty">補充依頼はまだありません</td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>
  </div>
</template>

<style scoped>
.content {
  flex: 1;
  padding: 40px;
}

.panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(150px, 1fr));
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
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

.wide {
  grid-column: span 2;
}

button {
  border: none;
  background: #ff7a00;
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
  font-weight: 800;
  cursor: pointer;
}

button.secondary {
  background: #e2e8f0;
  color: #334155;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

h2 {
  margin: 0 0 16px;
  font-size: 20px;
  font-weight: 800;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid #eef2f7;
  text-align: left;
}

.status {
  display: inline-block;
  border-radius: 999px;
  padding: 5px 10px;
  font-weight: 800;
  font-size: 12px;
}

.requested {
  background: #dbeafe;
  color: #1d4ed8;
}
.working {
  background: #fef3c7;
  color: #92400e;
}
.completed {
  background: #dcfce7;
  color: #15803d;
}
.cancelled {
  background: #fee2e2;
  color: #b91c1c;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.empty,
.muted {
  color: #64748b;
}

.error {
  color: #b91c1c;
  background: #fee2e2;
  padding: 10px 12px;
  border-radius: 8px;
}
</style>
