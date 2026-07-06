/**
 * 我的订单页面
 */
const { get, post } = require('../../utils/request')
const { formatDateTime, orderStatusMap } = require('../../utils/format')

Page({
  data: { orders: [], currentTab: -1, statusMap: orderStatusMap },

  onShow() {
    if (!wx.getStorageSync('token')) { wx.redirectTo({ url: '/pages/login/login' }); return }
    this.loadOrders()
  },

  switchTab(e) {
    this.setData({ currentTab: Number(e.currentTarget.dataset.status) })
    this.loadOrders()
  },

  async loadOrders() {
    try {
      const params = { page: 1, page_size: 50 }
      if (this.data.currentTab >= 0) params.status = this.data.currentTab
      const res = await get('/order/my/list', params)
      const orders = (res.data?.list || []).map(o => ({
        ...o,
        create_time: formatDateTime(o.create_time),
      }))
      this.setData({ orders })
    } catch (e) {}
  },

  async payOrder(e) {
    try {
      await post(`/order/pay/${e.currentTarget.dataset.id}`)
      wx.showToast({ title: '支付成功', icon: 'success' })
      this.loadOrders()
    } catch (err) {}
  },
})
