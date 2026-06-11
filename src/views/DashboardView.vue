<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div>
    <h1>ダッシュボード</h1>

    <p>権限：{{ auth.role }}</p>

    <div v-if="auth.role === 'admin'">
      <button>ユーザー管理</button>
      <button>売上データ削除</button>
    </div>

    <div v-if="auth.role === 'leader'">
      <button>売上確認</button>
      <button>集計</button>
    </div>

    <div v-if="auth.role === 'subleader'">
      <button>データ確認</button>
    </div>

    <div v-if="auth.role === 'viewer'">
      <p>閲覧のみ可能</p>
    </div>
  </div>
</template>
