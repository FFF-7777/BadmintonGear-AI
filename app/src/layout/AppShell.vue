<template>
  <div class="app-shell">
    <SideBar />
    <div class="main">
      <TopBar />
      <div class="content" :class="{ 'content--chat': route.name === 'Chat' }">
        <router-view v-slot="{ Component }">
          <keep-alive :include="['Home', 'Brands']">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import SideBar from '@/components/SideBar.vue'
import TopBar from '@/components/TopBar.vue'

const route = useRoute()
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  background: var(--bg-page);
}
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.content--chat {
  overflow: hidden;
}

@media (max-width: 900px) {
  .app-shell {
    display: block;
    height: 100vh;
    overflow-y: auto;
  }

  .main {
    height: auto;
    min-height: 100vh;
  }

  .content {
    overflow: visible;
  }
}
</style>
