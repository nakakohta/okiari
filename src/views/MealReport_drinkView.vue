<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { mastersService, reportService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { MealReport, Product, Store } from '@/lib/types'
import MDTable from '@/components/RestockTable/MDTable.vue'

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

</script>


<template>
  <div class="layout">
    <Sidebar />
    <main class="content">
      <AppHeader title="食数報告(ドリンク)" description="場所・商品ごとの食数を登録します。" />
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <!-- 1階・VIP・その他 -->
      <section class="table-section">
        <h2>1階・VIP・その他売店</h2>
        <MDTable/>
      </section>

      <!-- 2階 -->
      <section class="table-section">
        <h2>2階売店</h2>
        <MDTable/>
      </section>

      <!-- 3階 -->
      <section class="table-section">
        <h2>3階売店</h2>
        <MDTable/>
      </section>
    </main>
  </div>
</template>


<style scoped>
.content {
  flex: 1;
  padding: 40px;
}

h2 {
  margin: 0 0 16px;
  font-size: 20px;
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

.table-section{
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 32px;
}

.table-section h2{
  margin: 0 0 20px;
  font-size: 22px;
  font-weight: bold;
}
</style>
