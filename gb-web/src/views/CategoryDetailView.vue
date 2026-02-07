<template>
  <div class="page">
    <router-link to="/categories" class="back">← 返回分类列表</router-link>
    <template v-if="detail">
      <div class="card meta-card">
        <h1 class="detail-title">{{ detail.categoryName }}</h1>
        <p class="meta-code">食品分类号：{{ detail.categoryCode }}</p>
      </div>

      <!-- 分组展示：本级 / 继承自父级 / 适量使用 -->
      <template v-if="hasGrouped">
        <section v-if="(detail.directAdditives?.length ?? 0) > 0" class="card table-wrap">
          <h2 class="section-title">本级允许使用的添加剂</h2>
          <p class="section-desc">表 A.1 中直接规定在该食品分类下的使用条款</p>
          <table class="data-table">
            <colgroup><col style="width: 20%" /><col style="width: 14%" /><col style="width: 22%" /><col style="width: 8%" /><col style="width: 8%" /><col style="width: 28%" /></colgroup>
            <thead><tr><th class="col-name">中文名称</th><th class="col-name">功能</th><th class="col-name">最大使用量/使用类型</th><th class="col-code">CNS</th><th class="col-code">INS</th><th class="col-name">备注</th></tr></thead>
            <tbody>
              <tr v-for="a in detail.directAdditives" :key="a.faid">
                <td class="col-name"><router-link :to="`/additives/${a.faid}`">{{ a.nameCn }}</router-link></td>
                <td class="col-name">{{ a.function || '—' }}</td>
                <td class="col-name">{{ formatMaxUsage(a.maxUsage ?? a.usageType, a.usageType) }}</td>
                <td class="col-code">{{ a.cns || '—' }}</td>
                <td class="col-code">{{ a.ins || '—' }}</td>
                <td class="col-name">{{ a.remark || a.residueNote || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </section>
        <section v-if="(detail.parentAdditives?.length ?? 0) > 0" class="card table-wrap">
          <h2 class="section-title">继承自父级分类允许使用的添加剂</h2>
          <p class="section-desc">因食品分类层级继承，从上级分类沿用至本分类的条款</p>
          <table class="data-table">
            <colgroup><col style="width: 20%" /><col style="width: 14%" /><col style="width: 22%" /><col style="width: 8%" /><col style="width: 8%" /><col style="width: 28%" /></colgroup>
            <thead><tr><th class="col-name">中文名称</th><th class="col-name">功能</th><th class="col-name">最大使用量/使用类型</th><th class="col-code">CNS</th><th class="col-code">INS</th><th class="col-name">备注</th></tr></thead>
            <tbody>
              <tr v-for="a in detail.parentAdditives" :key="a.faid">
                <td class="col-name"><router-link :to="`/additives/${a.faid}`">{{ a.nameCn }}</router-link></td>
                <td class="col-name">{{ a.function || '—' }}</td>
                <td class="col-name">{{ formatMaxUsage(a.maxUsage ?? a.usageType, a.usageType) }}</td>
                <td class="col-code">{{ a.cns || '—' }}</td>
                <td class="col-code">{{ a.ins || '—' }}</td>
                <td class="col-name">{{ a.remark || a.residueNote || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </section>
        <section v-if="(detail.gmpAdditives?.length ?? 0) > 0" class="card table-wrap">
          <h2 class="section-title">按生产需要适量使用的添加剂（表 A.2）</h2>
          <p class="section-desc">表 A.2 中适用于本分类的「按生产需要适量使用」品种</p>
          <table class="data-table">
            <colgroup><col style="width: 20%" /><col style="width: 14%" /><col style="width: 22%" /><col style="width: 8%" /><col style="width: 8%" /><col style="width: 28%" /></colgroup>
            <thead><tr><th class="col-name">中文名称</th><th class="col-name">功能</th><th class="col-name">最大使用量/使用类型</th><th class="col-code">CNS</th><th class="col-code">INS</th><th class="col-name">备注</th></tr></thead>
            <tbody>
              <tr v-for="a in detail.gmpAdditives" :key="a.faid">
                <td class="col-name"><router-link :to="`/additives/${a.faid}`">{{ a.nameCn }}</router-link></td>
                <td class="col-name">{{ a.function || '—' }}</td>
                <td class="col-name">{{ formatMaxUsage(a.maxUsage ?? a.usageType, a.usageType) }}</td>
                <td class="col-code">{{ a.cns || '—' }}</td>
                <td class="col-code">{{ a.ins || '—' }}</td>
                <td class="col-name">{{ a.remark || a.residueNote || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </template>

      <!-- 无分组数据时回退为单表 -->
      <div v-else class="card table-wrap">
        <h2 class="section-title">本分类下允许使用的添加剂</h2>
        <table class="data-table">
          <colgroup><col style="width: 20%" /><col style="width: 14%" /><col style="width: 22%" /><col style="width: 8%" /><col style="width: 8%" /><col style="width: 28%" /></colgroup>
          <thead><tr><th class="col-name">中文名称</th><th class="col-name">功能</th><th class="col-name">最大使用量/使用类型</th><th class="col-code">CNS</th><th class="col-code">INS</th><th class="col-name">备注</th></tr></thead>
          <tbody>
            <tr v-for="a in detail.additives" :key="a.faid">
              <td class="col-name"><router-link :to="`/additives/${a.faid}`">{{ a.nameCn }}</router-link></td>
              <td class="col-name">{{ a.function || '—' }}</td>
              <td class="col-name">{{ formatMaxUsage(a.maxUsage ?? a.usageType, a.usageType) }}</td>
              <td class="col-code">{{ a.cns || '—' }}</td>
              <td class="col-code">{{ a.ins || '—' }}</td>
              <td class="col-name">{{ a.remark || a.residueNote || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
    <p v-else-if="loading" class="loading">加载中…</p>
    <p v-else class="empty">未找到该分类</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api, type CategoryDetail } from '../api/client'
import { formatMaxUsage } from '../utils/formatUsage'

const route = useRoute()
const detail = ref<CategoryDetail | null>(null)
const loading = ref(true)

const hasGrouped = computed(() => {
  const d = detail.value
  if (!d) return false
  return (
    (d.directAdditives?.length ?? 0) > 0 ||
    (d.parentAdditives?.length ?? 0) > 0 ||
    (d.gmpAdditives?.length ?? 0) > 0
  )
})

onMounted(async () => {
  const code = route.params.code as string
  if (!code) { loading.value = false; return }
  try {
    detail.value = await api.getCategory(decodeURIComponent(code))
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
.detail-title { font-size: 1.35rem; margin: 0 0 0.25rem; }
.meta-code { margin: 0; font-size: 0.9rem; color: var(--color-text-muted); }
.section-title { margin: 0; padding: 1rem 1rem 0; font-size: 1rem; color: var(--color-text-muted); }
.section-desc { margin: 0.25rem 1rem 0; padding: 0; font-size: 0.85rem; color: var(--color-text-muted); }
.table-wrap { overflow-x: auto; padding: 0 0 1rem; }
.loading, .empty { padding: 1.5rem; margin: 0; color: var(--color-text-muted); }
</style>
