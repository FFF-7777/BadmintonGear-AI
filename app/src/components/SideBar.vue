<template>
  <aside class="sidebar">
    <button class="brand" @click="go('/home')">
      <AiMark class="brand-mark" :size="52" />
      <span class="brand-copy">
        <b>羽智选</b>
        <small>BadmintonGear AI</small>
      </span>
    </button>

    <button class="ask-card" @click="go('/chat')">
      <span class="ask-mark">AI</span>
      <span class="ask-copy">
        <b>问问装备怎么选</b>
        <small>预算、打法、水平，一句话对比</small>
      </span>
    </button>

    <nav class="nav">
      <span class="nav-title">导航</span>
      <button
        v-for="item in navs"
        :key="item.path"
        class="nav-item"
        :class="{ active: isActive(item) }"
        @click="go(item.path)"
      >
        <span class="nav-ico">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div class="brand-list">
      <span class="nav-title">热门品牌</span>
      <button
        v-for="b in brands"
        :key="b.id"
        class="brand-link"
        :class="{ active: route.params.id === b.id && route.name === 'BrandDetail' }"
        @click="go(`/brand/${b.id}`)"
      >
        <img :src="b.logo" :alt="`${b.name} logo`" />
        <span>{{ b.nameCn }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import AiMark from '@/components/AiMark.vue'
import { brands } from '@/data/knowledge'

const route = useRoute()
const router = useRouter()

const navs = [
  { path: '/home', label: 'AI 选品', icon: '✦' },
  { path: '/brands', label: '装备库', icon: '▦' },
  { path: '/chat', label: 'AI 问答', icon: '◐' },
]

function go(p) {
  if (route.fullPath !== p) router.push(p)
}

function isActive(item) {
  if (item.path === '/home') return route.path === '/home' || route.path === '/'
  return route.path.startsWith(item.path)
}
</script>

<style scoped>
.sidebar {
  width: 248px;
  flex: 0 0 248px;
  height: calc(100vh - 20px);
  margin: 10px 0 10px 10px;
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
  color: var(--text-primary);
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.66);
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(28px) saturate(1.25);
}

.brand,
.ask-card,
.nav-item,
.brand-link {
  width: 100%;
  border: 0;
  cursor: pointer;
  font: inherit;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 6px 18px;
  text-align: left;
  background: transparent;
}

.ask-mark {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #07111f;
  background: var(--sport-gradient);
}

.brand-mark {
  box-shadow: none;
}

.brand-copy b,
.brand-copy small,
.ask-copy b,
.ask-copy small {
  display: block;
}

.brand-copy b {
  font-size: 20px;
  font-weight: 950;
  letter-spacing: 0;
}

.brand-copy small,
.ask-copy small {
  color: var(--text-tertiary);
}

.brand-copy small {
  margin-top: 2px;
  font-size: 12px;
}

.ask-card {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 90px;
  margin-bottom: 18px;
  padding: 14px;
  text-align: left;
  color: var(--text-primary);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(236, 254, 255, 0.72)),
    linear-gradient(145deg, rgba(217, 249, 157, 0.42), rgba(253, 164, 175, 0.18));
  box-shadow: var(--shadow-sm);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.ask-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.ask-mark {
  width: 44px;
  height: 44px;
  border-radius: 16px;
  font-weight: 950;
}

.ask-copy b {
  font-size: 15px;
  font-weight: 950;
}

.ask-copy small {
  margin-top: 4px;
  line-height: 1.45;
}

.nav,
.brand-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.brand-list {
  flex: 1;
  min-height: 0;
  margin-top: 20px;
  overflow-y: auto;
}

.nav-title {
  padding: 0 10px 2px;
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 900;
}

.nav-item,
.brand-link {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 46px;
  padding: 10px 12px;
  color: var(--text-secondary);
  text-align: left;
  border-radius: 17px;
  background: transparent;
  transition: transform 0.16s ease, background 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}

.nav-item:hover,
.brand-link:hover {
  transform: translateX(2px);
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.72);
}

.nav-item.active,
.brand-link.active {
  color: #07111f;
  font-weight: 900;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.nav-ico {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 11px;
  background: rgba(236, 254, 255, 0.9);
  color: var(--primary-2);
  font-weight: 950;
}

.brand-link img {
  width: 54px;
  height: 28px;
  object-fit: contain;
  flex: 0 0 auto;
}

.brand-link span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .sidebar {
    width: auto;
    height: auto;
    min-height: 0;
    margin: 10px;
    padding: 14px;
  }

  .brand,
  .ask-card {
    display: none;
  }

  .nav {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }

  .nav-title,
  .brand-list {
    display: none;
  }

  .nav-item {
    justify-content: center;
    min-height: 44px;
  }
}
</style>
