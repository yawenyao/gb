<template>
  <div class="home">
    <section class="hero">
      <h1 class="hero-title">食品添加剂使用标准</h1>
      <p class="hero-desc">GB 2760-2024 综合查询 · 按添加剂或按食品分类双向查询</p>
    </section>
    <section class="intro card">
      <h2>使用原则</h2>
      <div class="intro-text" v-if="siteRules.full_intro">{{ siteRules.full_intro }}</div>
      <p v-else class="loading">加载中…</p>
      <p v-if="siteRules.data_update_notice" class="update-notice">{{ siteRules.data_update_notice }}</p>
    </section>
    <section class="quick-links">
      <h2>快速入口</h2>
      <div class="links-grid">
        <router-link to="/additives" class="quick-card card">
          <span class="quick-icon">📋</span>
          <span class="quick-label">食品添加剂查询</span>
          <span class="quick-hint">表 A.1 添加剂列表与使用范围</span>
        </router-link>
        <router-link to="/categories" class="quick-card card">
          <span class="quick-icon">🏷️</span>
          <span class="quick-label">按食品名称查询</span>
          <span class="quick-hint">表 A.2 食品分类与可用添加剂</span>
        </router-link>
        <router-link to="/processing-aids" class="quick-card card">
          <span class="quick-icon">⚙️</span>
          <span class="quick-label">加工助剂</span>
          <span class="quick-hint">食品工业用加工助剂</span>
        </router-link>
        <router-link to="/enzymes" class="quick-card card">
          <span class="quick-icon">🧪</span>
          <span class="quick-label">酶制剂</span>
          <span class="quick-hint">酶制剂名单与来源</span>
        </router-link>
        <router-link to="/spices" class="quick-card card">
          <span class="quick-icon">🌸</span>
          <span class="quick-label">香精香料</span>
          <span class="quick-hint">B.1/B.2/B.3 香精香料</span>
        </router-link>
        <router-link to="/appendix-d" class="quick-card card">
          <span class="quick-icon">D</span>
          <span class="quick-label">附录D</span>
          <span class="quick-hint">食品添加剂功能类别定义</span>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api/client'

const siteRules = ref<Record<string, unknown>>({})

onMounted(async () => {
  try {
    siteRules.value = await api.getSiteRules()
  } catch {
    siteRules.value = { full_intro: '暂无使用原则文本，请查看标准原文。' }
  }
})
</script>

<style scoped>
.hero {
  text-align: center;
  margin-bottom: 2.5rem;
}
.hero-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
  color: var(--color-text);
}
.hero-desc {
  color: var(--color-text-muted);
  margin: 0;
  font-size: 1rem;
}
.intro {
  padding: 1.5rem;
  margin-bottom: 2rem;
}
.intro h2 {
  font-size: 1.1rem;
  margin: 0 0 1rem;
  color: var(--color-primary);
}
.intro-text {
  white-space: pre-wrap;
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--color-text-muted);
  max-height: 20em;
  overflow-y: auto;
}
.loading {
  color: var(--color-text-muted);
}
.update-notice {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  font-size: 0.85rem;
  color: var(--color-accent);
}
.quick-links h2 {
  font-size: 1.1rem;
  margin: 0 0 1rem;
  color: var(--color-text-muted);
}
.links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
.quick-card {
  display: flex;
  flex-direction: column;
  padding: 1.25rem;
  text-decoration: none;
  color: inherit;
  transition: border-color var(--transition), transform var(--transition);
}
.quick-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
}
.quick-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}
.quick-label {
  font-weight: 600;
  margin-bottom: 0.25rem;
}
.quick-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}
</style>
