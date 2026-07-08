/**
 * AI客服悬浮按钮组件（可拖动）
 */
Component({
  data: {
    x: 0, // 左上角横坐标(px)
    y: 0, // 左上角纵坐标(px)
    _startX: 0, // 触摸起始时按钮位置
    _startY: 0,
    _touchX: 0, // 触摸起始时手指位置
    _touchY: 0,
    _moved: false, // 本次触摸是否发生拖动
    _btnW: 96, // 按钮宽高(px)，attached 中按 rpx 换算
    _btnH: 96,
    _winW: 375,
    _winH: 667,
  },

  lifetimes: {
    attached() {
      const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync()
      const winW = info.windowWidth
      const winH = info.windowHeight
      const pxPerRpx = winW / 750
      const btnSize = 96 * pxPerRpx // 按钮为 96rpx

      // 读取上次保存的位置，保证跨页面一致
      const saved = wx.getStorageSync('ai_float_pos')
      let x, y
      if (saved && typeof saved.x === 'number') {
        x = saved.x
        y = saved.y
      } else {
        // 默认位置：右下角，距右边 24rpx，距底部 200rpx（避开 tabBar）
        x = winW - btnSize - 24 * pxPerRpx
        y = winH - btnSize - 200 * pxPerRpx
      }

      this.setData({
        x,
        y,
        _btnW: btnSize,
        _btnH: btnSize,
        _winW: winW,
        _winH: winH,
      })
    },
  },

  methods: {
    onTouchStart(e) {
      const t = e.touches[0]
      this.setData({
        _startX: this.data.x,
        _startY: this.data.y,
        _touchX: t.clientX,
        _touchY: t.clientY,
        _moved: false,
      })
    },

    onTouchMove(e) {
      const t = e.touches[0]
      const dx = t.clientX - this.data._touchX
      const dy = t.clientY - this.data._touchY
      if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
        this.setData({ _moved: true })
      }
      // 限幅，确保按钮不超出屏幕
      let nx = this.data._startX + dx
      let ny = this.data._startY + dy
      nx = Math.max(0, Math.min(nx, this.data._winW - this.data._btnW))
      ny = Math.max(0, Math.min(ny, this.data._winH - this.data._btnH))
      this.setData({ x: nx, y: ny })
    },

    onTouchEnd() {
      if (this.data._moved) {
        // 拖动结束，保存位置供其他页面复用
        wx.setStorageSync('ai_float_pos', { x: this.data.x, y: this.data.y })
      }
    },

    goChat() {
      // 若为拖动操作，则不触发跳转
      if (this.data._moved) return
      const token = wx.getStorageSync('token')
      if (!token) {
        wx.showToast({ title: '请先登录', icon: 'none' })
        setTimeout(() => {
          wx.navigateTo({ url: '/pages/login/login' })
        }, 1000)
        return
      }
      wx.navigateTo({ url: '/pages/chat/chat' })
    },
  },
})
