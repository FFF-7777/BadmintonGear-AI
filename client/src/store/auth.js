/**
 * 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const username = ref(localStorage.getItem('admin_username') || '')
  const nickname = ref(localStorage.getItem('admin_nickname') || '')
  const avatar = ref(localStorage.getItem('admin_avatar') || '')

  /** 设置登录信息 */
  function setLogin(data) {
    token.value = data.token
    username.value = data.username
    nickname.value = data.nickname || data.username
    avatar.value = data.avatar || ''
    localStorage.setItem('admin_token', data.token)
    localStorage.setItem('admin_username', data.username)
    localStorage.setItem('admin_nickname', data.nickname || data.username)
    localStorage.setItem('admin_avatar', data.avatar || '')
  }

  /** 更新资料信息(昵称、头像) */
  function setProfile(data) {
    if (data.nickname !== undefined) {
      nickname.value = data.nickname || username.value
      localStorage.setItem('admin_nickname', nickname.value)
    }
    if (data.avatar !== undefined) {
      avatar.value = data.avatar || ''
      localStorage.setItem('admin_avatar', avatar.value)
    }
  }

  /** 退出登录 */
  function logout() {
    token.value = ''
    username.value = ''
    nickname.value = ''
    avatar.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_username')
    localStorage.removeItem('admin_nickname')
    localStorage.removeItem('admin_avatar')
  }

  /** 是否已登录 */
  function isLoggedIn() {
    return !!token.value
  }

  return { token, username, nickname, avatar, setLogin, setProfile, logout, isLoggedIn }
})
