<template>
  <div class="page">
    <h1 class="page-title">香精香料查询</h1>
    <p class="page-desc">使用原则、表 B.1 不得添加香精香料的食品名单、B.2 天然香料、B.3 合成香料</p>
    <div v-if="rules && Object.keys(rules).length" class="card intro-block">
      <h2>使用原则</h2>
      <pre class="rules-text">{{ rulesText }}</pre>
    </div>
    <div class="tabs">
      <button :class="['tab', activeTab === 'b1' ? 'active' : '']" @click="activeTab = 'b1'">表 B.1 不得添加的食品</button>
      <button :class="['tab', activeTab === 'b2' ? 'active' : '']" @click="activeTab = 'b2'">表 B.2 天然香料</button>
      <button :class="['tab', activeTab === 'b3' ? 'active' : '']" @click="activeTab = 'b3'">表 B.3 合成香料</button>
    </div>
    <div v-show="activeTab === 'b1'" class="card table-wrap">
      <table class="data-table">
        <colgroup>
          <col style="width: 14%" />
          <col style="width: 86%" />
        </colgroup>
        <thead>
          <tr>
            <th class="col-code">食品分类号</th>
            <th class="col-name">食品名称</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in spicesB1" :key="i">
            <td class="col-code">{{ row.category_code || '—' }}</td>
            <td class="col-name">{{ row.category_name || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-show="activeTab === 'b2'" class="card table-wrap">
      <table class="data-table">
        <colgroup>
          <col style="width: 12%" />
          <col style="width: 18%" />
          <col style="width: 18%" />
          <col style="width: 10%" />
          <col style="width: 10%" />
          <col style="width: 32%" />
        </colgroup>
        <thead>
          <tr>
            <th class="col-name">类别</th>
            <th class="col-name">中文名称</th>
            <th class="col-name">英文名称</th>
            <th class="col-code">编码</th>
            <th class="col-code">FEMA</th>
            <th class="col-name">备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in spicesB2" :key="i">
            <td class="col-name">{{ row.category || '—' }}</td>
            <td class="col-name">{{ row.name_cn || '—' }}</td>
            <td class="col-name">{{ row.name_en || '—' }}</td>
            <td class="col-code">{{ row.code || '—' }}</td>
            <td class="col-code">{{ row.fema || '—' }}</td>
            <td class="col-name">{{ row.remarks || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-show="activeTab === 'b3'" class="card table-wrap">
      <table class="data-table">
        <colgroup>
          <col style="width: 12%" />
          <col style="width: 18%" />
          <col style="width: 18%" />
          <col style="width: 10%" />
          <col style="width: 10%" />
          <col style="width: 32%" />
        </colgroup>
        <thead>
          <tr>
            <th class="col-name">类别</th>
            <th class="col-name">中文名称</th>
            <th class="col-name">英文名称</th>
            <th class="col-code">编码</th>
            <th class="col-code">FEMA</th>
            <th class="col-name">备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in spicesB3" :key="i">
            <td class="col-name">{{ row.category || '—' }}</td>
            <td class="col-name">{{ row.name_cn || '—' }}</td>
            <td class="col-name">{{ row.name_en || '—' }}</td>
            <td class="col-code">{{ row.code || '—' }}</td>
            <td class="col-code">{{ row.fema || '—' }}</td>
            <td class="col-name">{{ row.remarks || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="loading" class="loading">加载中…</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api } from '../api/client'

const rules = ref<Record<string, unknown>>({})
const spicesB1 = ref<Record<string, unknown>[]>([])
const spicesB2 = ref<Record<string, unknown>[]>([])
const spicesB3 = ref<Record<string, unknown>[]>([])
const loading = ref(true)
const activeTab = ref<'b1' | 'b2' | 'b3'>('b1')

const rulesText = computed(() => {
  if (!rules.value) return ''
  const t = rules.value.principles ?? rules.value.full_intro ?? ''
  return typeof t === 'string' ? t : JSON.stringify(t, null, 2)
})

onMounted(async () => {
  try {
    const [r, b1, b2, b3] = await Promise.all([
      api.getSpicesRules().catch(() => ({})),
      api.getSpicesB1(),
      api.getSpicesB2(),
      api.getSpicesB3(),
    ])
    rules.value = r
    spicesB1.value = b1
    spicesB2.value = b2
    spicesB3.value = b3
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title { font-size: 1.5rem; margin: 0 0 0.25rem; }
.page-desc { color: var(--color-text-muted); margin: 0 0 1.5rem; font-size: 0.9rem; }
.intro-block { padding: 1.5rem; margin-bottom: 1.5rem; }
.intro-block h2 { font-size: 1rem; margin: 0 0 0.75rem; color: var(--color-text-muted); }
.rules-text { white-space: pre-wrap; font-size: 0.85rem; margin: 0; color: var(--color-text-muted); max-height: 12em; overflow-y: auto; }
.tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.tab { padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid var(--color-border); background: var(--color-surface); color: var(--color-text-muted); cursor: pointer; }
.tab:hover { color: var(--color-text); }
.tab.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.table-wrap { overflow-x: auto; padding: 0; }
.loading { padding: 1.5rem; margin: 0; color: var(--color-text-muted); }
</style>
