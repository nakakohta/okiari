<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { mastersService, reportService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { InventoryCheck, Product, Store } from '@/lib/types'

const auth = useAuthStore()
const stores = ref<Store[]>([])
const products = ref<Product[]>([])
const checks = ref<InventoryCheck[]>([])
const checkDate = ref(new Date().toISOString().slice(0, 10))
const storeId = ref<number | ''>('')
const productId = ref<number | ''>('')
const expectedQuantity = ref<string>('')
const actualQuantity = ref(0)
const isConfirmed = ref(false)
const note = ref('')
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')

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
    products.value = productData
    checks.value = checkData
  } catch {
    errorMessage.value = '棚卸情報を取得できませんでした'
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
    await reportService.createInventoryCheck({
      check_date: checkDate.value,
      store_id: Number(storeId.value),
      product_id: Number(productId.value),
      expected_quantity: expectedQuantity.value === '' ? null : Number(expectedQuantity.value),
      actual_quantity: actualQuantity.value,
      is_confirmed: isConfirmed.value,
      note: note.value || null,
    })
    expectedQuantity.value = ''
    actualQuantity.value = 0
    isConfirmed.value = false
    note.value = ''
    await load()
  } catch {
    errorMessage.value = '棚卸結果を保存できませんでした'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="layout">
    <Sidebar />
    <main class="content">
      <AppHeader title="棚卸" description="現在在庫と実棚の差異を記録します。" />
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <form class="panel form-grid" @submit.prevent="save">
        <label>
          日付
          <input v-model="checkDate" type="date" required />
        </label>
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
          期待数量
          <input v-model="expectedQuantity" type="number" min="0" placeholder="未入力なら現在在庫" />
        </label>
        <label>
          実数量
          <input v-model.number="actualQuantity" type="number" min="0" required />
        </label>
        <label class="checkbox">
          <input v-model="isConfirmed" type="checkbox" />
          在庫へ反映する
        </label>
        <label class="wide">
          メモ
          <input v-model="note" type="text" placeholder="任意" />
        </label>
        <button type="submit" :disabled="saving || !auth.canEditReports">
          {{ auth.canEditReports ? (saving ? '保存中...' : '保存') : '閲覧のみ' }}
        </button>
      </form>

      <section class="panel">
        <h2>棚卸一覧</h2>
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
            </tr>
            <tr v-if="checks.length === 0">
              <td colspan="7" class="empty">棚卸結果はまだありません</td>
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
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

.checkbox {
  flex-direction: row;
  align-items: center;
  min-height: 40px;
}

.wide {
  grid-column: span 2;
}

button {
  border: none;
  background: #ff7a00;
  color: white;
  padding: 11px 16px;
  border-radius: 8px;
  font-weight: 800;
  cursor: pointer;
}

button:disabled {
  opacity: 0.55;
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
  color: #b91c1c;
  background: #fee2e2;
  padding: 10px 12px;
  border-radius: 8px;
}
</style>
