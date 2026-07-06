/**
 * 编辑收货地址
 */
const { get, post, put } = require('../../utils/request')

Page({
  data: {
    id: 0,
    name: '',
    phone: '',
    address: '',
    isDefault: false,
    saving: false,
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ id: Number(options.id) })
      wx.setNavigationBarTitle({ title: '编辑地址' })
      this.loadDetail(options.id)
    }
  },

  async loadDetail(id) {
    try {
      const res = await get(`/address/${id}`)
      const item = res.data
      this.setData({
        name: item.name,
        phone: item.phone,
        address: item.address,
        isDefault: item.is_default === 1,
      })
    } catch (e) {}
  },

  onName(e) { this.setData({ name: e.detail.value.trim() }) },
  onPhone(e) { this.setData({ phone: e.detail.value.trim() }) },
  onAddress(e) { this.setData({ address: e.detail.value.trim() }) },
  onDefaultChange(e) { this.setData({ isDefault: e.detail.value }) },

  validate() {
    const { name, phone, address } = this.data
    if (!name) {
      wx.showToast({ title: '请输入收货人', icon: 'none' })
      return false
    }
    if (!phone) {
      wx.showToast({ title: '请输入联系电话', icon: 'none' })
      return false
    }
    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '手机号格式不正确', icon: 'none' })
      return false
    }
    if (!address) {
      wx.showToast({ title: '请输入详细地址', icon: 'none' })
      return false
    }
    return true
  },

  async saveAddress() {
    if (!this.validate()) return

    const { id, name, phone, address, isDefault } = this.data
    const payload = {
      name,
      phone,
      address,
      is_default: isDefault ? 1 : 0,
    }

    this.setData({ saving: true })
    try {
      if (id) {
        await put(`/address/${id}`, payload)
        wx.showToast({ title: '更新成功', icon: 'success' })
      } else {
        await post('/address', payload)
        wx.showToast({ title: '添加成功', icon: 'success' })
      }
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) {} finally {
      this.setData({ saving: false })
    }
  },
})
