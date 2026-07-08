<template>
  <header class="topbar" :class="{ 'topbar--chat': isChat }">
    <div class="crumb">
      <button @click="go('/home')">羽智选</button>
      <span>/</span>
      <b>{{ currentTitle }}</b>
    </div>

    <template v-if="!isChat">
      <form class="search" :class="{ focused }" @submit.prevent="submit">
        <span class="search-ico">⌕</span>
        <input
          v-model="kw"
          class="search-input"
          placeholder="输入预算、打法、品牌，让 AI 帮你选"
          @focus="focused = true"
          @blur="focused = false"
        />
        <button class="search-btn" type="submit">问 AI</button>
      </form>

      <button class="top-ask" @click="go('/chat')">AI 选品</button>
    </template>

    <div v-else class="topbar-note">
      <span>型号对比、参数解释、热身训练都可以直接问</span>
    </div>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const kw = ref('')
const focused = ref(false)

const titleMap = {
  Home: 'AI 选品',
  Brands: '装备库',
  Chat: 'AI 问答',
  BrandDetail: '品牌详情',
  Article: '装备详情',
}

const currentTitle = computed(() => titleMap[route.name] || 'AI 选品')
const isChat = computed(() => route.name === 'Chat')

function go(p) {
  router.push(p)
}

function submit() {
  const q = kw.value.trim()
  router.push(q ? `/chat?q=${encodeURIComponent(q)}` : '/chat')
}
</script>

<style scoped>
.topbar {
  height: 74px;
  flex: 0 0 74px;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 10px 34px 10px 24px;
  z-index: 10;
  background: rgba(247, 250, 252, 0.72);
  backdrop-filter: blur(22px) saturate(1.2);
}

.topbar--chat {
  justify-content: space-between;
}

.crumb {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  min-width: 154px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.crumb button {
  padding: 0;
  color: var(--text-tertiary);
  border: 0;
  background: transparent;
  cursor: pointer;
  font-weight: 800;
}

.crumb b {
  color: var(--text-primary);
  font-weight: 950;
}

.search {
  flex: 1;
  max-width: 620px;
  height: 46px;
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 auto;
  padding: 0 7px 0 16px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}

.search.focused {
  transform: translateY(-1px);
  border-color: rgba(34, 211, 238, 0.64);
  box-shadow: 0 0 0 5px rgba(34, 211, 238, 0.12), var(--shadow-md);
}

.search-ico {
  color: var(--text-tertiary);
  font-size: 18px;
  font-weight: 900;
}

.search-input {
  flex: 1;
  min-width: 0;
  color: var(--text-primary);
  border: 0;
  outline: 0;
  background: transparent;
}

.search-btn,
.top-ask {
  border: 0;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 950;
}

.search-btn {
  height: 34px;
  padding: 0 16px;
  color: #07111f;
  background: var(--sport-gradient);
}

.top-ask {
  flex: 0 0 auto;
  height: 44px;
  padding: 0 18px;
  color: #07111f;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: var(--shadow-sm);
}

.topbar-note {
  color: #7b8ca1;
  font-size: 13px;
  font-weight: 800;
}

@media (max-width: 900px) {
  .topbar {
    height: auto;
    flex-wrap: wrap;
    padding: 4px 14px 14px;
  }

  .crumb {
    width: 100%;
  }

  .search {
    order: 3;
    width: 100%;
    max-width: none;
  }

  .topbar-note {
    width: 100%;
  }
}
</style>
