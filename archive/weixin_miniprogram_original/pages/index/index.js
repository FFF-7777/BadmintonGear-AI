/**
 * 首页
 */
const { get } = require('../../utils/request')
const { downloadImageFields } = require('../../utils/image')

Page({
  data: {
    banners: [],
    products: [],
    serviceList: [
      { icon: '🛡', name: '正品保障', desc: '官方正品', colorClass: 'purple' },
      { icon: '🚚', name: '极速发货', desc: '闪电发货', colorClass: 'blue' },
      { icon: '⭐', name: '7天无忧退', desc: '放心购物', colorClass: 'orange' },
      { icon: '🎯', name: 'AI 智选', desc: '智能推荐', colorClass: 'cyan' }
    ]
  },

  onShow() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    this.loadData()
  },

  /** 加载轮播图和装备 */
  async loadData() {
    try {
      const [bannerRes, productRes] = await Promise.all([
        get('/banner/list'),
        get('/product/list', { page: 1, page_size: 20 }),
      ])
      // 用 wx.downloadFile 下载图片到本地，真机才能渲染 <image>
      const banners = await downloadImageFields(bannerRes.data || [], 'image')
      const products = await downloadImageFields(productRes.data?.list || [], 'image')
      this.setData({ banners, products })
    } catch (e) {}
  },

  /** 跳转装备详情 */
  goDetail(e) {
    wx.navigateTo({ url: `/pages/detail/detail?id=${e.currentTarget.dataset.id}` })
  },

  /** 快捷加入购物车 */
  async addCartQuick(e) {
    const id = e.currentTarget.dataset.id
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/login/login' }); return }
    try {
      await require('../../utils/request').post('/cart/add', { product_id: id, quantity: 1 })
      wx.showToast({ title: '已加购物车', icon: 'success' })
    } catch (err) {
      wx.showToast({ title: err.message || '添加失败', icon: 'none' })
    }
  },
})
