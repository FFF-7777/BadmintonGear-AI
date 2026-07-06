<template>
  <div class="login-page">
    <div class="login-bg">
      <span class="bg-circle bg-circle-1"></span>
      <span class="bg-circle bg-circle-2"></span>
      <span class="bg-circle bg-circle-3"></span>
    </div>

    <div class="login-wrapper">
      <!-- 左侧品牌区 -->
      <div class="login-brand">
        <div class="brand-content">
          <div class="brand-logo">
            <el-icon :size="36"><Shop /></el-icon>
          </div>
          <h1 class="brand-title">羽毛球装备导购</h1>
          <p class="brand-desc">基于 LangChain 的羽毛球装备智能导购管理系统</p>
          <ul class="brand-features">
            <li><el-icon><ChatDotRound /></el-icon><span>AI 智能客服</span></li>
            <li><el-icon><Goods /></el-icon><span>装备与订单管理</span></li>
            <li><el-icon><DataAnalysis /></el-icon><span>数据可视化看板</span></li>
          </ul>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="login-panel">
        <div class="panel-header">
          <h2>管理员登录</h2>
          <p>欢迎回来，请登录您的管理账号</p>
        </div>

        <el-form
          :model="form"
          :rules="rules"
          ref="formRef"
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              size="large"
              clearable
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <p class="panel-footer">© {{ currentYear }} 羽毛球装备导购 · 管理后台</p>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 管理员登录页面
 */
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLogin } from '@/api/auth'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref(null)
const loading = ref(false)
const currentYear = computed(() => new Date().getFullYear())

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

/** 处理登录 */
async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await adminLogin(form)
    auth.setLogin(res.data)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(135deg, #eef2f7 0%, #dce4ef 100%);
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.35;
}

.bg-circle-1 {
  width: 480px;
  height: 480px;
  top: -120px;
  right: -80px;
  background: radial-gradient(circle, #409eff 0%, transparent 70%);
}

.bg-circle-2 {
  width: 320px;
  height: 320px;
  bottom: -60px;
  left: -40px;
  background: radial-gradient(circle, #304156 0%, transparent 70%);
}

.bg-circle-3 {
  width: 200px;
  height: 200px;
  top: 40%;
  left: 30%;
  background: radial-gradient(circle, #67c23a 0%, transparent 70%);
  opacity: 0.15;
}

.login-wrapper {
  position: relative;
  display: flex;
  width: 100%;
  max-width: 900px;
  min-height: 520px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(48, 65, 86, 0.18);
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 左侧品牌区 */
.login-brand {
  flex: 1;
  background: linear-gradient(160deg, #304156 0%, #263445 100%);
  padding: 48px 40px;
  display: flex;
  align-items: center;
  color: #fff;
}

.brand-content {
  width: 100%;
}

.brand-logo {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(64, 158, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
  margin-bottom: 24px;
}

.brand-title {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.brand-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.65);
  line-height: 1.6;
  margin-bottom: 36px;
}

.brand-features {
  list-style: none;
  padding: 0;
  margin: 0;
}

.brand-features li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-features li:last-child {
  border-bottom: none;
}

.brand-features .el-icon {
  color: #409eff;
  font-size: 18px;
}

/* 右侧登录区 */
.login-panel {
  flex: 1;
  background: #fff;
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.panel-header {
  margin-bottom: 32px;
}

.panel-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
}

.panel-header p {
  font-size: 14px;
  color: #909399;
}

.login-form {
  width: 100%;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 8px;
  padding: 4px 12px;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 16px;
  letter-spacing: 4px;
  margin-top: 8px;
}

.panel-footer {
  margin-top: 32px;
  text-align: center;
  font-size: 12px;
  color: #c0c4cc;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-wrapper {
    flex-direction: column;
    max-width: 420px;
    min-height: auto;
  }

  .login-brand {
    padding: 32px 28px;
  }

  .brand-desc {
    margin-bottom: 20px;
  }

  .brand-features {
    display: none;
  }

  .login-panel {
    padding: 32px 28px;
  }
}
</style>
