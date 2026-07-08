/**
 * 小程序入口
 */
App({
  globalData: {
    userInfo: null,
    token: '',
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
  },
})
