<template>

  <div class="layout">

    <Sidebar />

    <main class="content">

      <!-- header -->

      <div class="header">

        <div>
          <h1>ユーザ管理</h1>

          <p>
            管理者・リーダー・サブリーダー・閲覧専用ユーザの権限を確認できます
          </p>
        </div>

        <button class="add-btn">
          ユーザ追加
        </button>

      </div>

      <!-- cards -->

      <div class="cards">

        <div class="card">
          <h3>管理者</h3>
          <h2 class="orange">10名</h2>
          <p>上限人数</p>
        </div>

        <div class="card">
          <h3>リーダー</h3>
          <h2 class="blue">40名</h2>
          <p>上限人数</p>
        </div>

        <div class="card">
          <h3>サブリーダー</h3>
          <h2 class="green">10名</h2>
          <p>上限人数</p>
        </div>

        <div class="card">
          <h3>閲覧専用</h3>
          <h2 class="gray">10名</h2>
          <p>上限人数</p>
        </div>

      </div>

      <!-- table -->

      <div class="table-card">

        <h2>ユーザー一覧</h2>

        <table>

          <thead>
            <tr>
              <th>名前</th>
              <th>権限</th>
              <th>担当</th>
              <th>状態</th>
              <th>最終更新</th>
            </tr>
          </thead>

          <tbody>

            <tr>
              <td>山田 太郎</td>
              <td class="leader">リーダー</td>
              <td>フード売店</td>
              <td>
                <span class="status active-status">
                  有効
                </span>
              </td>
              <td>18:05</td>
            </tr>

            <tr>
              <td>佐藤 花子</td>
              <td class="sub">サブリーダー</td>
              <td>ドリンク補充</td>
              <td>
                <span class="status active-status">
                  有効
                </span>
              </td>
              <td>17:58</td>
            </tr>

            <tr>
              <td>比嘉 一郎</td>
              <td class="admin">管理者</td>
              <td>全体管理</td>
              <td>
                <span class="status active-status">
                  有効
                </span>
              </td>
              <td>17:31</td>
            </tr>

          </tbody>

        </table>

      </div>

    </main>

  </div>

</template>

<script setup>
import Sidebar from '../components/Sidebar.vue'
</script>

<style scoped>

.content {
  flex: 1;
  padding: 40px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  font-size: 40px;
  margin-bottom: 10px;
}

.header p {
  color: #6b7280;
}

.add-btn {
  background: #ff7a00;
  color: white;
  border: none;
  padding: 14px 30px;
  border-radius: 14px;
  cursor: pointer;
}

.cards {
  display: flex;
  gap: 20px;
  margin-top: 40px;
}

.card {
  background: white;
  width: 220px;
  padding: 25px;
  border-radius: 20px;
}

.card h2 {
  font-size: 36px;
}

.orange {
  color: #ff7a00;
}

.blue {
  color: #2563ff;
}

.green {
  color: #16a34a;
}

.gray {
  color: #6b7280;
}

.table-card {
  background: white;
  margin-top: 40px;
  padding: 30px;
  border-radius: 24px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

th,
td {
  padding: 18px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

thead {
  background: #f1f5f9;
}

.admin {
  color: red;
  font-weight: bold;
}

.leader {
  color: #2563ff;
  font-weight: bold;
}

.sub {
  color: #16a34a;
  font-weight: bold;
}

.status {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
}

.active-status {
  background: #dcfce7;
  color: #16a34a;
}

</style>