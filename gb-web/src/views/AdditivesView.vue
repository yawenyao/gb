<template>
  <div class="page">
    <h1 class="page-title">食品添加剂查询</h1>
    <p class="page-desc">表 A.1 允许使用的食品添加剂品种、使用范围及最大使用量或残留量</p>
    <div class="toolbar card">
      <input
        v-model="query"
        type="search"
        placeholder="搜索中文名、英文名或 CNS 号…"
        class="search-input"
        @input="onSearch"
      />
    </div>
    <div class="card table-wrap">
      <table class="data-table">
        <colgroup>
          <col style="width: 20%" />
          <col style="width: 18%" />
          <col style="width: 8%" />
          <col style="width: 8%" />
          <col style="width: 26%" />
          <col style="width: 20%" />
        </colgroup>
        <thead>
          <tr>
            <th class="col-name">中文名称</th>
            <th class="col-name">英文名称</th>
            <th class="col-code">CNS 号</th>
            <th class="col-code">INS 号</th>
            <th class="col-name">功能</th>
            <th class="col-action">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in list" :key="a.faid">
            <td class="col-name">{{ a.nameCn }}</td>
            <td class="col-name">{{ a.nameEn || '—' }}</td>
            <td class="col-code">{{ a.cns || '—' }}</td>
            <td class="col-code">{{ a.ins || '—' }}</td>
            <td class="col-name">{{ a.function || '—' }}</td>
            <td class="col-action">
              <router-link :to="`/additives/${a.faid}`" class="btn btn-primary btn-sm">查看</router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="loading" class="loading">加载中…</p>
      <p v-else-if="list.length === 0" class="empty">暂无数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Additive } from '../api/client'

const list = ref<Additive[]>([])
const loading = ref(true)
const query = ref('')
let searchTimer: ReturnType<typeof setTimeout>

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchList, 200)
}

async function fetchList() {
  loading.value = true
  try {
    list.value = await api.getAdditives(query.value || undefined)
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.page-title { font-size: 1.5rem; margin: 0 0 0.25rem; }
.page-desc { color: var(--color-text-muted); margin: 0 0 1.5rem; font-size: 0.9rem; }
.toolbar { padding: 0.75rem 1rem; margin-bottom: 1rem; }
.search-input {
  width: 100%;
  max-width: 400px;
  padding: 0.6rem 1rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text);
}
.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
}
.table-wrap { overflow-x: auto; padding: 0; }
.loading, .empty { padding: 1.5rem; margin: 0; color: var(--color-text-muted); text-align: center; }
</style>
