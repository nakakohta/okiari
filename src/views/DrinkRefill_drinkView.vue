<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { mastersService, reportService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { Product, RestockReport, RestockStatus, Store } from '@/lib/types'
import DTable from '@/components/RestockTable/DTable.vue'

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
    <div class="meal-report">

      <!-- 目次 -->
      <div class="store-menu">
        <h1>売店一覧</h1>

        <div class="store-links">
          <a href="#csl">CSL</a>
          <a href="#store2-1">2-1</a>
          <a href="#store2-2">2-2</a>
          <a href="#store2-7">2-7</a>
          <a href="#store2-8">2-8</a>
          <a href="#store3-1">3-1</a>
          <a href="#store3-5">3-5</a>
          <a href="#store3-9">3-9</a>
          <a href="#store3-11">3-11</a>
        </div>
      </div>

      <!-- CSL -->
      <section id="csl" class="store-section">
        <h2 class="store-title">
          CSL（コートサイドラウンジ）
        </h2>

        <h3>ドリンク補充</h3>
        <DTable title="ドリンク補充" />


        <h3>消耗品補充</h3>
        <DTable title="ドリンク補充" />
      </section>

      <!-- 2-1 -->
      <section id="store2-1" class="store-section">
        <h2 class="store-title">2-1</h2>

        <h3>ドリンク補充</h3>
        <DTable title="ドリンク補充" />

        <h3>消耗品補充</h3>
        <DTable title="ドリンク補充" />
      </section>

      <!-- 2-2 -->
      <section id="store2-2" class="store-section">
        <h2 class="store-title">2-2</h2>

        <h3>ドリンク補充</h3>
        <DTable title="ドリンク補充" />

        <h3>消耗品補充</h3>
        <DTable title="ドリンク補充" />
      </section>

      <!-- 2-7 -->
      <section id="store2-7" class="store-section">
        <h2 class="store-title">2-7</h2>

        <h3>ドリンク補充</h3>
        <DTable title="ドリンク補充" />

        <h3>消耗品補充</h3>
        <DTable title="ドリンク補充" />
      </section>

      <!-- 2-8 -->
      <section id="store2-8" class="store-section">
        <h2 class="store-title">2-8</h2>

        <h3>ドリンク補充</h3>
        <DTable title="ドリンク補充" />

        <h3>消耗品補充</h3>
        <DTable title="ドリンク補充" />
      </section>

      <!-- 3-1 -->
      <section id="store3-1" class="store-section">
        <h2 class="store-title">3-1</h2>

        <h3>ドリンク補充</h3>
        <DTable title="ドリンク補充" />

        <h3>消耗品補充</h3>
        <DTable title="ドリンク補充" />
      </section>

      <!-- 3-5 -->
      <section id="store3-5" class="store-section">
        <h2 class="store-title">3-5</h2>

          <h3>ドリンク補充</h3>
          <DTable title="ドリンク補充" />

          <h3>消耗品補充</h3>
          <DTable title="ドリンク補充" />
        </section>

        <!-- 3-9 -->
        <section id="store3-9" class="store-section">
          <h2 class="store-title">3-9</h2>

          <h3>ドリンク補充</h3>
          <DTable title="ドリンク補充" />

          <h3>消耗品補充</h3>
          <DTable title="ドリンク補充" />
        </section>

        <!-- 3-11 -->
        <section id="store3-11" class="store-section">
          <h2 class="store-title">
            3-11（スイートラウンジ）
          </h2>

          <h3>ドリンク補充</h3>
          <DTable title="ドリンク補充" />

          <h3>消耗品補充</h3>
          <DTable title="ドリンク補充" />
        </section>
      </div>
      </main>
    </div>
</template>

<style scoped>
.layout{
  display:flex;
  min-height:100vh;
}
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
.meal-report {
  padding: 30px;
  background: #f5f7fa;
}

.store-menu {
  background: white;
  padding: 25px;
  border-radius: 12px;
  margin-bottom: 40px;
}

.store-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 15px;
}

.store-links a {
  text-decoration: none;
  background: #2f6df6;
  color: white;
  padding: 10px 18px;
  border-radius: 8px;
}

.store-section {
  margin-bottom: 80px;
}

.store-title {
  font-size: 32px;
  margin-bottom: 25px;
  border-left: 6px solid #2f6df6;
  padding-left: 15px;
}

h3 {
  margin-top: 30px;
  margin-bottom: 15px;
}

html {
  scroll-behavior: smooth;
}

</style>
