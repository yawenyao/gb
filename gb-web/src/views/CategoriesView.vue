<template>
  <div class="page">
    <h1 class="page-title">按食品名称查询</h1>
    <p class="page-desc">表 A.2 食品分类号与名称，点击可查看该分类下允许使用的添加剂及使用细则</p>
    <div class="toolbar card">
      <input
        v-model="query"
        type="search"
        placeholder="搜索分类号或食品名称…"
        class="search-input"
        @input="onSearch"
      />
    </div>
    <div class="card table-wrap">
      <table class="data-table">
        <colgroup>
          <col style="width: 14%" />
          <col style="width: 56%" />
          <col style="width: 30%" />
        </colgroup>
        <thead>
          <tr>
            <th class="col-code">食品分类号</th>
            <th class="col-name">食品名称</th>
            <th class="col-action">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in list" :key="c.categoryCode">
            <td class="col-code">{{ c.categoryCode }}</td>
            <td class="col-name">{{ c.categoryName }}</td>
            <td class="col-action">
              <router-link :to="`/categories/${encodeURIComponent(c.categoryCode)}`" class="btn btn-primary btn-sm">查看添加剂</router-link>
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
import { api, type Category } from '../api/client'

const list = ref<Category[]>([])
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
    list.value = await api.getCategories(query.value || undefined)
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
.table-wrap { overflow-x: auto; padding: 0; }
.loading, .empty { padding: 1.5rem; margin: 0; color: var(--color-text-muted); text-align: center; }
</style>
