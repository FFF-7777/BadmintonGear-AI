/**
 * 首页
 */
const { get } = require('../../utils/request')
const { downloadImageFields } = require('../../utils/image')

Page({
  data: { banners: [], products: [] },

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
})
