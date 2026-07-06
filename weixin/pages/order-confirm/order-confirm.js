/**
 * 确认订单页面(模拟支付)
 */
const { get, post } = require('../../utils/request')

Page({
  data: {
    items: [],
    selectedAddress: null,
    receiverName: '',
    receiverPhone: '',
    receiverAddress: '',
    remark: '',
    loading: false,
  },

  onLoad(options) {
    if (options.items) {
      this.setData({ items: JSON.parse(options.items) })
    }
  },

  onShow() {
    if (!this.data.selectedAddress) {
      this.loadDefaultAddress()
    }
  },

  async loadDefaultAddress() {
    try {
      const res = await get('/address/default')
      if (res.data) {
        this.applyAddress(res.data)
      }
    } catch (e) {}
  },

  applyAddress(addr) {
    this.setData({
      selectedAddress: addr,
      receiverName: addr.name,
      receiverPhone: addr.phone,
      receiverAddress: addr.address,
    })
  },

  selectAddress() {
    wx.navigateTo({
      url: '/pages/address-list/address-list?select=1',
      events: {
        selectAddress: (addr) => {
          this.applyAddress(addr)
        },
      },
    })
  },

  onRemark(e) { this.setData({ remark: e.detail.value }) },

  /** 提交订单并模拟支付 */
  async submitOrder() {
    const { items, receiverName, receiverPhone, receiverAddress, remark } = this.data
    if (!receiverName || !receiverPhone || !receiverAddress) {
      wx.showToast({ title: '请选择收货地址', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    try {
      const res = await post('/order/create', {
        items,
        receiver_name: receiverName,
        receiver_phone: receiverPhone,
        receiver_address: receiverAddress,
        remark,
      })
      await post(`/order/pay/${res.data.id}`)
      wx.showToast({ title: '支付成功', icon: 'success' })
      setTimeout(() => wx.redirectTo({ url: '/pages/order-list/order-list' }), 1500)
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },
})
