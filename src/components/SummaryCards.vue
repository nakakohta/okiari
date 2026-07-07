<script setup lang="ts">
withDefaults(
  defineProps<{
    adminCount: number
    leaderCount: number
    subLeaderCount: number
    viewerCount: number
  }>(),
  {
    adminCount: 0,
    leaderCount: 0,
    subLeaderCount: 0,
    viewerCount: 0,
  },
)
</script>

<template>
  <div class="cards">
    <div class="card">
      <h3>管理者</h3>
      <strong class="orange">{{ adminCount }}名</strong>
      <p>全体管理</p>
    </div>
    <div class="card">
      <h3>リーダー</h3>
      <strong class="blue">{{ leaderCount }}名</strong>
      <p>業務編集</p>
    </div>
    <div class="card">
      <h3>サブリーダー</h3>
      <strong class="green">{{ subLeaderCount }}名</strong>
      <p>業務編集</p>
    </div>
    <div class="card">
      <h3>閲覧専用</h3>
      <strong class="gray">{{ viewerCount }}名</strong>
      <p>閲覧のみ</p>
    </div>
  </div>
</template>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 16px;
  margin: 28px 0;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.card h3 {
  margin: 0 0 10px;
  color: #475569;
  font-size: 14px;
  font-weight: 700;
}

.card strong {
  display: block;
  font-size: 30px;
  line-height: 1.2;
}

.card p {
  margin: 8px 0 0;
  color: #94a3b8;
  font-size: 12px;
}

.orange {
  color: #ff7a00;
}
.blue {
  color: #2563eb;
}
.green {
  color: #16a34a;
}
.gray {
  color: #64748b;
}
</style>
