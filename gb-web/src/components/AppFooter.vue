<template>
  <footer class="footer">
    <div class="footer-inner">
      <p class="disclaimer">
        本数据库仅供参考，食品添加剂使用范围和使用量的确定请以 GB 2760-2024 标准文本及相关公告为准。
      </p>
      <p class="copy">GB 2760 综合查询 · 复刻项目</p>
    </div>
  </footer>
</template>

<script setup lang="ts"></script>

<style scoped>
.footer {
  margin-top: auto;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  padding: 1.5rem;
}
.footer-inner {
  max-width: 1280px;
  margin: 0 auto;
  text-align: center;
}
.disclaimer {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: 0 0 0.5rem;
  line-height: 1.5;
}
.copy {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  opacity: 0.8;
  margin: 0;
}
</style>
