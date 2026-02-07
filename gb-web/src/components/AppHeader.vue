<template>
  <header class="header">
    <div class="header-inner">
      <router-link to="/" class="logo">
        <span class="logo-title">GB 2760</span>
        <span class="logo-sub">食品添加剂使用标准 · 综合查询</span>
      </router-link>
      <nav class="nav">
        <router-link to="/additives" class="nav-link">食品添加剂查询</router-link>
        <router-link to="/categories" class="nav-link">按食品名称查询</router-link>
        <router-link to="/processing-aids" class="nav-link">加工助剂</router-link>
        <router-link to="/enzymes" class="nav-link">酶制剂</router-link>
        <router-link to="/spices" class="nav-link">香精香料</router-link>
        <router-link to="/appendix-d" class="nav-link">附录D</router-link>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts"></script>

<style scoped>
.header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}
.logo {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: var(--color-text);
}
.logo:hover {
  color: var(--color-primary);
}
.logo-title {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--color-primary);
}
.logo-sub {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-top: 0.15rem;
}
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}
.nav-link {
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  color: var(--color-text-muted);
  transition: background var(--transition), color var(--transition);
}
.nav-link:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text);
}
.nav-link.router-link-active {
  background: rgba(37, 99, 235, 0.12);
  color: var(--color-primary);
}
</style>
