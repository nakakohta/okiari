<template>
  <div class="app-container">
    <RouterView />
  </div>
</template>

<style>
/* 画面全体の一番シンプルな共通スタイル */
html, body {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: sans-serif;
  background-color: #f3f4f6;
  color: #333;
}

*, *:before, *:after {
  box-sizing: inherit; /* 要素の幅や高さの計算を狂わせない設定 */
}

/* アシスト設定 */
.layout {
  display: flex;
  min-height: 100vh;
  width: 100%;
}
</style>
