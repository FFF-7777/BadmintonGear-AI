<template>
  <el-container class="layout-container">
    <el-aside width="236px" class="layout-aside">
      <div class="brand">
        <div class="brand-mark">羽</div>
        <div>
          <strong>羽智选</strong>
          <span>BadmintonGear AI</span>
        </div>
      </div>

      <el-menu :default-active="route.path" router class="side-menu">
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/product">
          <el-icon><Goods /></el-icon>
          <span>装备管理</span>
        </el-menu-item>
        <el-menu-item index="/category">
          <el-icon><Menu /></el-icon>
          <span>品类管理</span>
        </el-menu-item>
        <el-menu-item index="/user">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/banner">
          <el-icon><Picture /></el-icon>
          <span>内容位管理</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><Setting /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="content-frame">
      <el-header class="layout-header">
        <div>
          <span class="page-eyebrow">ADMIN CONSOLE</span>
          <h1>{{ route.meta.title }}</h1>
        </div>
        <div class="header-right">
          <div class="user-info" @click="router.push('/profile')">
            <el-avatar :size="36" :src="auth.avatar" class="header-avatar">
              {{ avatarFallback }}
            </el-avatar>
            <span class="user-name">{{ auth.nickname || auth.username || '管理员' }}</span>
          </div>
          <el-button class="logout-btn" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const avatarFallback = computed(() => {
  const name = auth.nickname || auth.username || '管'
  return name.charAt(0).toUpperCase()
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
  background:
    linear-gradient(135deg, rgba(217, 249, 157, 0.28), rgba(34, 211, 238, 0.12) 42%, rgba(251, 113, 133, 0.1)),
    #f7f9fc;
}

.layout-aside {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 18px 14px;
  overflow-y: auto;
  border-right: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(22px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 8px 22px;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  color: #08111f;
  font-size: 20px;
  font-weight: 900;
  border-radius: 16px;
  background: linear-gradient(135deg, #d9f99d, #67e8f9);
  box-shadow: 0 12px 26px rgba(34, 211, 238, 0.24);
}

.brand strong,
.brand span {
  display: block;
}

.brand strong {
  color: #0f172a;
  font-size: 18px;
}

.brand span {
  margin-top: 3px;
  color: #64748b;
  font-size: 12px;
}

.side-menu {
  border-right: 0;
  background: transparent;
}

.side-menu :deep(.el-menu-item) {
  height: 46px;
  margin: 4px 0;
  color: #475569;
  border-radius: 14px;
}

.side-menu :deep(.el-menu-item:hover) {
  color: #0f172a;
  background: rgba(15, 23, 42, 0.05);
}

.side-menu :deep(.el-menu-item.is-active) {
  color: #0f172a;
  font-weight: 800;
  background: #fff;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.content-frame {
  min-width: 0;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 84px;
  padding: 18px 28px 10px;
  background: transparent;
}

.page-eyebrow {
  color: #64748b;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0;
}

.layout-header h1 {
  margin: 4px 0 0;
  color: #0f172a;
  font-size: 24px;
  line-height: 1.15;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 44px;
  padding: 4px 10px 4px 4px;
  cursor: pointer;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.user-info:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
}

.header-avatar {
  color: #08111f;
  font-weight: 800;
  background: linear-gradient(135deg, #d9f99d, #67e8f9);
}

.user-name {
  max-width: 120px;
  overflow: hidden;
  color: #334155;
  font-size: 14px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-btn {
  height: 40px;
  padding: 0 16px;
  color: #0f172a;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
}

.layout-main {
  padding: 14px 28px 28px;
  overflow-y: auto;
}

@media (max-width: 900px) {
  .layout-container {
    display: block;
  }

  .layout-aside {
    position: relative;
    width: 100% !important;
    height: auto;
  }

  .side-menu {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .layout-header {
    height: auto;
    align-items: flex-start;
    gap: 16px;
    flex-direction: column;
  }

  .layout-main {
    padding: 12px 14px 22px;
  }
}
</style>
