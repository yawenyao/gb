<template>
  <div class="page">
    <h1 class="page-title">酶制剂查询</h1>
    <p class="page-desc">酶制剂名单、来源与供体</p>
    <div class="card table-wrap">
      <table class="data-table">
        <colgroup>
          <col style="width: 18%" />
          <col style="width: 18%" />
          <col style="width: 22%" />
          <col style="width: 22%" />
          <col style="width: 20%" />
        </colgroup>
        <thead>
          <tr>
            <th class="col-name">中文名称</th>
            <th class="col-name">英文名称</th>
            <th class="col-name">来源</th>
            <th class="col-name">供体</th>
            <th class="col-name">备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in list" :key="i">
            <td class="col-name">{{ row.name_cn || '—' }}</td>
            <td class="col-name">{{ row.name_en || '—' }}</td>
            <td class="col-name">{{ row.source || '—' }}</td>
            <td class="col-name">{{ row.donor || '—' }}</td>
            <td class="col-name">{{ row.remarks || '—' }}</td>
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
    list.value = await api.getEnzymes()
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
