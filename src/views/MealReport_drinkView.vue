<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { mastersService, reportService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { MealReport, Product, Store } from '@/lib/types'

const auth = useAuthStore()
const stores = ref<Store[]>([])
const products = ref<Product[]>([])
const reports = ref<MealReport[]>([])
const reportDate = ref(new Date().toISOString().slice(0, 10))
const storeId = ref<number | ''>('')
const productId = ref<number | ''>('')
const quantity = ref(0)
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
      mastersService.products('meal'),
      reportService.mealReports(),
    ])
    stores.value = storeData
    products.value = productData
    reports.value = reportData
  } catch {
    errorMessage.value = '食数報告情報を取得できませんでした'
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
    await reportService.createMealReport({
      report_date: reportDate.value,
      store_id: Number(storeId.value),
      product_id: Number(productId.value),
      quantity: quantity.value,
      note: note.value || null,
    })
    quantity.value = 0
    note.value = ''
    await load()
  } catch {
    errorMessage.value = '食数報告を保存できませんでした'
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
      <AppHeader title="食数報告(ドリンク)" description="場所・商品ごとの食数を登録します。" />
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <form class="panel form-grid" @submit.prevent="save">
        <table>
  <thead>
    <tr>
      <th>操作</th>
      <th>商品名</th>
      <th>前回数</th>
      <th>追加数</th>
      <th>備考</th>
    </tr>
  </thead>

  <tbody>
    <tr
      v-for="(item, index) in items"
      :key="index"
    >
      <td>
        <button
          class="delete-btn"
          @click="deleteRow(index)"
        >
          削除
        </button>
      </td>

      <td>
        <input
          v-model="item.name"
          placeholder="商品名"
        />
      </td>

      <td>
        <input
          type="number"
          v-model.number="item.previous"
        />
      </td>

      <td>
        <input
          type="number"
          v-model.number="item.add"
        />
      </td>

      <td>
        <input
          v-model="item.memo"
          placeholder="備考"
        />
      </td>
    </tr>
  </tbody>
</table>
      </form>
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
