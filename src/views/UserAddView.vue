<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
// 仮でヘッダーを追加
import AppHeader from '@/components/AppHeader.vue'

const router = useRouter()

// 入力項目
const name = ref('')
const email = ref('')
const role = ref('viewer') // 初期値は閲覧権限

// テスト用処理
const handleAddUser = () => {
  alert(`ユーザを登録しました！\n名前: ${name.value}\n権限: ${role.value}`)

  // 登録完了後は一覧画面に戻る
  router.push('/user-management')
}
</script>

<template>
  <!-- ページデザインは後々変更したい… -->
  <div class="layout">
    <main class="main-container">
      <!-- あとで書く追加ページ用のヘッダー作る -->
      <AppHeader
        title="ユーザー追加"
        description="ユーザー追加フォーム"
      />
      <div class="form-container">
        <form @submit.prevent="handleAddUser" class="add-form">
          <div class="input-group">
            <label>名前</label>
            <input v-model="name" type="text" placeholder="名前" required />
          </div>

          <div class="input-group">
            <label>メールアドレス</label>
            <input v-model="email" type="email" placeholder="example@example.com" required />
          </div>

          <div class="input-group">
            <label>所属権限</label>
            <select v-model="role">
              <option value="admin">管理者（admin）</option>
              <option value="leader">リーダー（leader）</option>
              <option value="sub-leader">サブリーダー（sub-leader）</option>
              <option value="viewer">一般スタッフ（viewer）</option>
            </select>

            <button type="submit" class="submit-btn">この内容で登録する</button>
          </div>
        </form>
      </div>
    </main>
  </div>
</template>

<style scoped>
.main-container {
  margin-left: 50px;
}

.main-content {
  flex: 1;
  padding: 40px;
  background-color: #f8f9fa;
}

.form-container {
  max-width: 600px;
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.back-btn {
  background-color: none;
  border: none;
  color: #718096;
  cursor: pointer;
  margin-bottom: 16px;
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 24px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-weight: 600;
  font-size: 14px;
}

.input-group input, .input-group select {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 15px;
}

.submit-btn {
  background-color: #ff7a00;
  color: white;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-weight: bold;
  font-size: 16px;
  cursor: pointer;
  margin-top: 12px;
}

.submit-btn:hover {
  background-color: #e66e00;
}
</style>
