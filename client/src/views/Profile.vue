<template>
  <div class="page-container profile-page">
    <el-row :gutter="20">
      <el-col :xs="24" :md="10">
        <el-card shadow="never" class="profile-card">
          <template #header>
            <span>基本信息</span>
          </template>
          <div class="avatar-section">
            <el-avatar :size="100" :src="profileForm.avatar" class="avatar-preview">
              {{ avatarFallback }}
            </el-avatar>
            <el-upload
              :show-file-list="false"
              :http-request="handleAvatarUpload"
              accept="image/*"
            >
              <el-button type="primary" size="small" :loading="uploading">更换头像</el-button>
            </el-upload>
            <p class="avatar-tip">支持 jpg / png / gif / webp，建议尺寸 200×200</p>
          </div>
          <el-form :model="profileForm" label-width="80px" class="profile-form">
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickname" placeholder="请输入昵称" maxlength="50" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="profileSaving" @click="handleSaveProfile">保存资料</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="14">
        <el-card shadow="never" class="profile-card">
          <template #header>
            <span>修改密码</span>
          </template>
          <el-form
            ref="pwdFormRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-width="100px"
            class="profile-form"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入原密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少6位" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="pwdSaving" @click="handleChangePassword">修改密码</el-button>
              <el-button @click="resetPwdForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/** 管理员个人中心：资料修改、头像上传、密码修改 */
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminProfile, updateAdminProfile, changeAdminPassword, uploadAvatar } from '@/api/admin'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const pwdFormRef = ref(null)
const uploading = ref(false)
const profileSaving = ref(false)
const pwdSaving = ref(false)

const profileForm = reactive({
  username: '',
  nickname: '',
  avatar: '',
})

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const avatarFallback = computed(() => {
  const name = profileForm.nickname || profileForm.username || '管'
  return name.charAt(0).toUpperCase()
})

const validateConfirm = (rule, value, callback) => {
  if (value !== pwdForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function loadProfile() {
  const res = await getAdminProfile()
  profileForm.username = res.data.username
  profileForm.nickname = res.data.nickname || res.data.username
  profileForm.avatar = res.data.avatar || ''
}

async function handleAvatarUpload({ file }) {
  uploading.value = true
  try {
    const res = await uploadAvatar(file)
    profileForm.avatar = res.data.url
    await updateAdminProfile({ avatar: profileForm.avatar })
    auth.setProfile({ avatar: profileForm.avatar })
    ElMessage.success('头像更新成功')
  } finally {
    uploading.value = false
  }
}

async function handleSaveProfile() {
  const nickname = profileForm.nickname.trim()
  if (!nickname) {
    ElMessage.warning('昵称不能为空')
    return
  }
  profileSaving.value = true
  try {
    const res = await updateAdminProfile({ nickname })
    auth.setProfile({ nickname: res.data.nickname })
    ElMessage.success('资料保存成功')
  } finally {
    profileSaving.value = false
  }
}

async function handleChangePassword() {
  await pwdFormRef.value.validate()
  pwdSaving.value = true
  try {
    await changeAdminPassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    resetPwdForm()
    auth.logout()
    window.location.href = '/login'
  } finally {
    pwdSaving.value = false
  }
}

function resetPwdForm() {
  pwdForm.old_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm_password = ''
  pwdFormRef.value?.clearValidate()
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-page {
  padding: 0;
}
.profile-card {
  margin-bottom: 20px;
}
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #ebeef5;
}
.avatar-preview {
  font-size: 36px;
  background: #409eff;
  color: #fff;
}
.avatar-tip {
  margin: 0;
  font-size: 12px;
  color: #909399;
}
.profile-form {
  max-width: 420px;
}
</style>
