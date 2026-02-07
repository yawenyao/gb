<template>
  <div class="page">
    <h1 class="page-title">加工助剂查询</h1>
    <p class="page-desc">食品工业用加工助剂名单及使用范围</p>
    <div class="card table-wrap">
      <table class="data-table">
        <colgroup>
          <col style="width: 20%" />
          <col style="width: 20%" />
          <col style="width: 14%" />
          <col style="width: 46%" />
        </colgroup>
        <thead>
          <tr>
            <th class="col-name">中文名称</th>
            <th class="col-name">英文名称</th>
            <th class="col-name">功能</th>
            <th class="col-name">使用范围</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in list" :key="i">
            <td class="col-name">{{ row.name_cn || '—' }}</td>
            <td class="col-name">{{ row.name_en || '—' }}</td>
            <td class="col-name">{{ row.function || '—' }}</td>
            <td class="col-name">{{ row.usage_scope || '—' }}</td>
          </tr>
        </tbody>
      </table>
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
    list.value = await api.getProcessingAids()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title { font-size: 1.5rem; margin: 0 0 0.25rem; }
.page-desc { color: var(--color-text-muted); margin: 0 0 1.5rem; font-size: 0.9rem; }
.table-wrap { overflow-x: auto; padding: 0; }
.loading, .empty { padding: 1.5rem; margin: 0; color: var(--color-text-muted); text-align: center; }
</style>
