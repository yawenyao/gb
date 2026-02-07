<template>
  <div class="page">
    <router-link to="/additives" class="back">← 返回添加剂列表</router-link>
    <template v-if="detail">
      <div class="card meta-card">
        <h1 class="detail-title">{{ detail.nameCn }}</h1>
        <dl class="meta-list">
          <dt>英文名</dt><dd>{{ detail.nameEn || '—' }}</dd>
          <dt>CNS</dt><dd>{{ detail.cns || '—' }}</dd>
          <dt>INS</dt><dd>{{ detail.ins || '—' }}</dd>
          <dt>功能</dt><dd>{{ detail.function || '—' }}</dd>
        </dl>
      </div>
      <div class="card table-wrap">
        <h2 class="section-title">使用范围与用量</h2>
        <table class="data-table">
          <colgroup>
            <col style="width: 12%" />
            <col style="width: 32%" />
            <col style="width: 28%" />
            <col style="width: 28%" />
          </colgroup>
          <thead>
            <tr>
              <th class="col-code">食品分类号</th>
              <th class="col-name">食品名称</th>
              <th class="col-name">最大使用量 / 使用类型</th>
              <th class="col-name">备注</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(u, i) in detail.usage" :key="i">
              <td class="col-code">{{ u.foodCategoryCode }}</td>
              <td class="col-name">{{ u.foodName }}</td>
              <td class="col-name">{{ formatMaxUsage(u.maxUsage ?? u.usageType, u.usageType) }}</td>
              <td class="col-name">{{ u.remark || u.residueNote || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
    <p v-else-if="loading" class="loading">加载中…</p>
    <p v-else class="empty">未找到该添加剂</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api, type AdditiveDetail } from '../api/client'
import { formatMaxUsage } from '../utils/formatUsage'

const route = useRoute()
const detail = ref<AdditiveDetail | null>(null)
const loading = ref(true)

onMounted(async () => {
  const faid = Number(route.params.faid)
  if (!faid) { loading.value = false; return }
  try {
    detail.value = await api.getAdditive(faid)
  } catch {
    detail.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.back { display: inline-block; margin-bottom: 1rem; font-size: 0.9rem; }
.meta-card { padding: 1.5rem; margin-bottom: 1.5rem; }
.detail-title { font-size: 1.35rem; margin: 0 0 1rem; }
.meta-list { display: grid; grid-template-columns: auto 1fr; gap: 0.35rem 1.5rem; margin: 0; font-size: 0.9rem; }
.meta-list dt { color: var(--color-text-muted); }
.section-title { margin: 0; padding: 1rem 1rem 0; font-size: 1rem; color: var(--color-text-muted); }
.table-wrap { overflow-x: auto; padding: 0 0 1rem; }
.loading, .empty { padding: 1.5rem; margin: 0; color: var(--color-text-muted); }
</style>
