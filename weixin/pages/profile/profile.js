/**
 * 个人资料 / 密码修改
 */
const { get, put, uploadFile } = require('../../utils/request')
const { resolveImage } = require('../../utils/image')

Page({
  data: {
    username: '',
    nickname: '',
    phone: '',
    avatar: '',
    avatarUrl: '',
    avatarText: 'U',
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
    profileSaving: false,
    pwdSaving: false,
    uploading: false,
  },

  onShow() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    this.loadProfile()
  },

  /** 加载用户资料 */
  async loadProfile() {
    try {
      const res = await get('/user/profile/me')
      const user = res.data
      const nickname = user.nickname || user.username || ''
      // 用 wx.downloadFile 下载头像，真机才能显示
      const avatarUrl = await resolveImage(user.avatar)
      this.setData({
        username: user.username || '',
        nickname,
        phone: user.phone || '',
        avatar: user.avatar || '',
        avatarUrl,
        avatarText: nickname ? nickname[0].toUpperCase() : 'U',
      })
      this.syncLocalUserInfo(user)
    } catch (e) {}
  },

  /** 同步本地缓存 */
  syncLocalUserInfo(user) {
    const cached = wx.getStorageSync('userInfo') || {}
    const userInfo = {
      ...cached,
      username: user.username,
      nickname: user.nickname,
      avatar: user.avatar,
      phone: user.phone,
    }
    wx.setStorageSync('userInfo', userInfo)
  },

  onNickname(e) { this.setData({ nickname: e.detail.value.trim() }) },
  onPhone(e) { this.setData({ phone: e.detail.value.trim() }) },
  onOldPassword(e) { this.setData({ oldPassword: e.detail.value }) },
  onNewPassword(e) { this.setData({ newPassword: e.detail.value }) },
  onConfirmPassword(e) { this.setData({ confirmPassword: e.detail.value }) },

  /** 选择并上传头像 */
  chooseAvatar() {
    if (this.data.uploading) return
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const filePath = res.tempFiles[0].tempFilePath
        this.uploadAvatar(filePath)
      },
    })
  },

  async uploadAvatar(filePath) {
    this.setData({ uploading: true })
    wx.showLoading({ title: '上传中...' })
    try {
      const res = await uploadFile('/upload/user/avatar', filePath)
      const avatar = res.data.url
      await put('/user/profile', { avatar })
      // 上传后的新头像也是远程路径，需下载到本地
      const avatarUrl = await resolveImage(avatar)
      const nickname = this.data.nickname || this.data.username
      this.setData({
        avatar,
        avatarUrl,
        avatarText: nickname ? nickname[0].toUpperCase() : 'U',
      })
      this.syncLocalUserInfo({
        username: this.data.username,
        nickname: this.data.nickname,
        avatar,
        phone: this.data.phone,
      })
      wx.showToast({ title: '头像更新成功', icon: 'success' })
    } catch (e) {} finally {
      wx.hideLoading()
      this.setData({ uploading: false })
    }
  },

  /** 保存资料 */
  async saveProfile() {
    const { nickname, phone } = this.data
    if (!nickname) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' })
      return
    }
    if (phone && !/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '手机号格式不正确', icon: 'none' })
      return
    }
    this.setData({ profileSaving: true })
    try {
      const res = await put('/user/profile', { nickname, phone: phone || '' })
      const user = res.data
      this.setData({
        nickname: user.nickname,
        phone: user.phone || '',
        avatarText: user.nickname ? user.nickname[0].toUpperCase() : 'U',
      })
      this.syncLocalUserInfo(user)
      wx.showToast({ title: '资料保存成功', icon: 'success' })
    } catch (e) {} finally {
      this.setData({ profileSaving: false })
    }
  },

  /** 修改密码 */
  async changePassword() {
    const { oldPassword, newPassword, confirmPassword } = this.data
    if (!oldPassword) {
      wx.showToast({ title: '请输入原密码', icon: 'none' })
      return
    }
    if (!newPassword) {
      wx.showToast({ title: '请输入新密码', icon: 'none' })
      return
    }
    if (newPassword.length < 6) {
      wx.showToast({ title: '新密码至少6位', icon: 'none' })
      return
    }
    if (newPassword !== confirmPassword) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' })
      return
    }
    this.setData({ pwdSaving: true })
    try {
      await put('/user/profile/password', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      wx.showToast({ title: '密码修改成功', icon: 'success' })
      this.setData({ oldPassword: '', newPassword: '', confirmPassword: '' })
      setTimeout(() => {
        wx.removeStorageSync('token')
        wx.removeStorageSync('userInfo')
        wx.redirectTo({ url: '/pages/login/login' })
      }, 1500)
    } catch (e) {} finally {
      this.setData({ pwdSaving: false })
    }
  },
})
