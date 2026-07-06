/**
 * 登录 / 注册页面
 */
const { post } = require('../../utils/request')

Page({
  data: {
    isRegister: false,
    username: 'user001',
    password: '123456',
    regUsername: '',
    nickname: '',
    phone: '',
    regPassword: '',
    confirmPassword: '',
    loading: false,
  },

  onLoad(options) {
    if (options.username) {
      this.setData({ username: decodeURIComponent(options.username) })
    }
    if (options.mode === 'register') {
      this.setData({ isRegister: true })
      wx.setNavigationBarTitle({ title: '用户注册' })
    }
  },

  onUsername(e) { this.setData({ username: e.detail.value }) },
  onPassword(e) { this.setData({ password: e.detail.value }) },
  onRegUsername(e) { this.setData({ regUsername: e.detail.value.trim() }) },
  onNickname(e) { this.setData({ nickname: e.detail.value.trim() }) },
  onPhone(e) { this.setData({ phone: e.detail.value.trim() }) },
  onRegPassword(e) { this.setData({ regPassword: e.detail.value }) },
  onConfirmPassword(e) { this.setData({ confirmPassword: e.detail.value }) },

  switchToRegister() {
    this.setData({ isRegister: true })
    wx.setNavigationBarTitle({ title: '用户注册' })
  },

  switchToLogin() {
    this.setData({ isRegister: false })
    wx.setNavigationBarTitle({ title: '登录' })
  },

  /** 用户登录 */
  async handleLogin() {
    const { username, password } = this.data
    if (!username || !password) {
      wx.showToast({ title: '请输入用户名和密码', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    try {
      const res = await post('/auth/user/login', { username, password })
      wx.setStorageSync('token', res.data.token)
      wx.setStorageSync('userInfo', res.data)
      getApp().globalData.token = res.data.token
      wx.switchTab({ url: '/pages/index/index' })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },

  /** 注册表单校验 */
  validateRegister() {
    const { regUsername, nickname, regPassword, confirmPassword, phone } = this.data

    if (!regUsername) {
      wx.showToast({ title: '请输入用户名', icon: 'none' })
      return false
    }
    if (!/^[a-zA-Z0-9_]{3,20}$/.test(regUsername)) {
      wx.showToast({ title: '用户名需3-20位字母数字或下划线', icon: 'none' })
      return false
    }
    if (!nickname) {
      wx.showToast({ title: '请输入昵称', icon: 'none' })
      return false
    }
    if (nickname.length > 20) {
      wx.showToast({ title: '昵称不能超过20个字符', icon: 'none' })
      return false
    }
    if (phone && !/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '手机号格式不正确', icon: 'none' })
      return false
    }
    if (!regPassword) {
      wx.showToast({ title: '请输入密码', icon: 'none' })
      return false
    }
    if (regPassword.length < 6) {
      wx.showToast({ title: '密码至少6位', icon: 'none' })
      return false
    }
    if (!confirmPassword) {
      wx.showToast({ title: '请确认密码', icon: 'none' })
      return false
    }
    if (regPassword !== confirmPassword) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' })
      return false
    }
    return true
  },

  /** 用户注册 */
  async handleRegister() {
    if (!this.validateRegister()) return

    const { regUsername, nickname, phone, regPassword } = this.data
    this.setData({ loading: true })
    try {
      await post('/auth/user/register', {
        username: regUsername,
        password: regPassword,
        nickname,
        phone: phone || undefined,
      })
      wx.showToast({ title: '注册成功', icon: 'success' })
      this.setData({
        isRegister: false,
        username: regUsername,
        password: '',
        regUsername: '',
        nickname: '',
        phone: '',
        regPassword: '',
        confirmPassword: '',
      })
      wx.setNavigationBarTitle({ title: '登录' })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },
})
