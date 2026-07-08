/**
 * 收货地址列表
 */
const { get, put, del } = require('../../utils/request')

Page({
  data: {
    list: [],
    selectMode: false,
  },

  onLoad(options) {
    const selectMode = options.select === '1'
    this.setData({ selectMode })
    if (selectMode) {
      wx.setNavigationBarTitle({ title: '选择收货地址' })
    }
  },

  onShow() {
    this.loadList()
  },

  stopBubble() {},

  async loadList() {
    try {
      const res = await get('/address/list')
      this.setData({ list: res.data || [] })
    } catch (e) {}
  },

  onTapItem(e) {
    if (!this.data.selectMode) return
    const item = e.currentTarget.dataset.item
    const eventChannel = this.getOpenerEventChannel()
    if (eventChannel && eventChannel.emit) {
      eventChannel.emit('selectAddress', item)
    }
    wx.navigateBack()
  },

  goAdd() {
    wx.navigateTo({ url: '/pages/address-edit/address-edit' })
  },

  goEdit(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/address-edit/address-edit?id=${id}` })
  },

  async setDefault(e) {
    const id = e.currentTarget.dataset.id
    try {
      await put(`/address/${id}/default`)
      wx.showToast({ title: '已设为默认', icon: 'success' })
      this.loadList()
    } catch (err) {}
  },

  removeAddress(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '提示',
      content: '确定删除该地址吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await del(`/address/${id}`)
            wx.showToast({ title: '删除成功', icon: 'success' })
            this.loadList()
          } catch (err) {}
        }
      },
    })
  },
})
