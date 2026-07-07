<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { reportService } from '@/lib/services'
import type { InventoryCheck, MealReport, RestockReport } from '@/lib/types'

const loading = ref(false)
const errorMessage = ref('')
const meals = ref<MealReport[]>([])
const refills = ref<RestockReport[]>([])
const inventoryChecks = ref<InventoryCheck[]>([])

const today = new Date().toISOString().slice(0, 10)

const todayMealTotal = computed(() =>
  meals.value.filter((report) => report.report_date === today).reduce((sum, report) => sum + report.quantity, 0),
)
const todayRefillCount = computed(
  () => refills.value.filter((report) => report.requested_at.slice(0, 10) === today).length,
)
const todayInventoryCount = computed(
  () => inventoryChecks.value.filter((report) => report.check_date === today).length,
)
const recentActivities = computed(() =>
  [
    ...meals.value.slice(0, 5).map((item) => ({
      type: '食数',
      title: `${item.store?.name || '-'} / ${item.product?.name || '-'}`,
      detail: `${item.quantity}${item.product?.unit || ''}`,
      date: item.created_at || item.report_date,
    })),
    ...refills.value.slice(0, 5).map((item) => ({
      type: '補充',
      title: `${item.store?.name || '-'} / ${item.product?.name || '-'}`,
      detail: `${item.quantity}${item.product?.unit || ''} / ${item.status}`,
      date: item.requested_at,
    })),
    ...inventoryChecks.value.slice(0, 5).map((item) => ({
      type: '棚卸',
      title: `${item.store?.name || '-'} / ${item.product?.name || '-'}`,
      detail: `差異 ${item.difference ?? item.actual_quantity - item.expected_quantity}`,
      date: item.created_at || item.check_date,
    })),
  ]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 10),
)

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [mealData, refillData, inventoryData] = await Promise.all([
      reportService.mealReports(),
      reportService.drinkRefills(),
      reportService.inventoryChecks(),
    ])
    meals.value = mealData
    refills.value = refillData
    inventoryChecks.value = inventoryData
  } catch {
    errorMessage.value = 'ダッシュボード情報を取得できませんでした'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="layout">
    <Sidebar />
    <main class="content">
      <AppHeader title="ダッシュボード" description="本日の業務状況と直近の報告を確認できます。" />

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <section class="summary-grid">
        <div class="summary-card">
          <span>本日の食数</span>
          <strong>{{ todayMealTotal }}</strong>
        </div>
        <div class="summary-card">
          <span>ドリンク補充</span>
          <strong>{{ todayRefillCount }}</strong>
        </div>
        <div class="summary-card">
          <span>棚卸件数</span>
          <strong>{{ todayInventoryCount }}</strong>
        </div>
      </section>

      <section class="panel">
        <h2>直近の報告</h2>
        <table>
          <thead>
            <tr>
              <th>種別</th>
              <th>内容</th>
              <th>詳細</th>
              <th>日時</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="activity in recentActivities" :key="`${activity.type}-${activity.date}-${activity.title}`">
              <td>{{ activity.type }}</td>
              <td>{{ activity.title }}</td>
              <td>{{ activity.detail }}</td>
              <td>{{ new Date(activity.date).toLocaleString() }}</td>
            </tr>
            <tr v-if="recentActivities.length === 0">
              <td colspan="4" class="empty">報告はまだありません</td>
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

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card,
.panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.summary-card {
  padding: 22px;
}

.summary-card span {
  display: block;
  color: #64748b;
  font-weight: 700;
}

.summary-card strong {
  display: block;
  margin-top: 8px;
  font-size: 36px;
  color: #172033;
}

.panel {
  padding: 24px;
}

.panel h2 {
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
