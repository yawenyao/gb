<template>
  <div class="page">
    <h1 class="page-title">附录D 食品添加剂功能类别定义</h1>
    <p class="page-desc">GB 2760 附录 D 中各类功能的定义说明</p>
    <div class="card list-card">
      <div v-for="(item, i) in list" :key="i" class="appendix-item">
        <span class="appendix-num">{{ item.number }}</span>
        <div class="appendix-body">
          <strong class="appendix-func">{{ item.function }}</strong>
          <p class="appendix-def">{{ item.definition }}</p>
        </div>
      </div>
    </div>
    <p v-if="loading" class="loading">加载中…</p>
    <p v-else-if="list.length === 0" class="empty">暂无数据</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api/client'

const list = ref<Record<string, unknown>[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    list.value = await api.getAppendixD()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title { font-size: 1.5rem; margin: 0 0 0.25rem; }
.page-desc { color: var(--color-text-muted); margin: 0 0 1.5rem; font-size: 0.9rem; }
.list-card { padding: 0; overflow: hidden; }
.appendix-item {
  display: flex;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}
.appendix-item:last-child { border-bottom: none; }
.appendix-num {
  flex-shrink: 0;
  font-weight: 700;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}
.appendix-body { flex: 1; }
.appendix-func { display: block; margin-bottom: 0.25rem; }
.appendix-def { margin: 0; font-size: 0.9rem; color: var(--color-text-muted); line-height: 1.5; }
.loading, .empty { padding: 1.5rem; margin: 0; color: var(--color-text-muted); }
</style>
