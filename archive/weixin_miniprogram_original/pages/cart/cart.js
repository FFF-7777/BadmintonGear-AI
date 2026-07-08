/**
 * 购物车页面
 */
const { get, put, del } = require('../../utils/request')
const { downloadImageFields } = require('../../utils/image')

Page({
  data: { cartList: [], totalPrice: '0.00', checkedCount: 0 },

  onShow() {
    if (!wx.getStorageSync('token')) { wx.redirectTo({ url: '/pages/login/login' }); return }
    this.loadCart()
  },

  async loadCart() {
    try {
      const res = await get('/cart/list')
      // 批量下载装备图片，真机才能显示
      const list = await downloadImageFields(res.data || [], 'product_image', 'product_image')
      this.setData({ cartList: list })
      this.calcTotal()
    } catch (e) {}
  },

  calcTotal() {
    const checked = this.data.cartList.filter(i => i.checked)
    const total = checked.reduce((s, i) => s + i.product_price * i.quantity, 0)
    this.setData({ totalPrice: total.toFixed(2), checkedCount: checked.length })
  },

  async toggleCheck(e) {
    const item = this.data.cartList.find(i => i.id === e.currentTarget.dataset.id)
    await put(`/cart/${item.id}`, { checked: item.checked ? 0 : 1 })
    this.loadCart()
  },

  async changeQty(e) {
    const { id, delta } = e.currentTarget.dataset
    const item = this.data.cartList.find(i => i.id === id)
    const qty = item.quantity + Number(delta)
    if (qty < 1) return
    await put(`/cart/${id}`, { quantity: qty })
    this.loadCart()
  },

  async deleteItem(e) {
    await del(`/cart/${e.currentTarget.dataset.id}`)
    wx.showToast({ title: '已删除', icon: 'success' })
    this.loadCart()
  },

  goSettle() {
    const checked = this.data.cartList.filter(i => i.checked)
    if (checked.length === 0) {
      wx.showToast({ title: '请选择装备', icon: 'none' })
      return
    }
    const items = checked.map(i => ({ product_id: i.product_id, quantity: i.quantity }))
    wx.navigateTo({ url: `/pages/order-confirm/order-confirm?items=${JSON.stringify(items)}` })
  },
})
