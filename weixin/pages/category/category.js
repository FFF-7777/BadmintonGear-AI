/**
 * 分类页面
 */
const { get } = require('../../utils/request')
const { downloadImageFields } = require('../../utils/image')

Page({
  data: { categories: [], currentCat: 0, products: [] },

  onShow() {
    if (!wx.getStorageSync('token')) { wx.redirectTo({ url: '/pages/login/login' }); return }
    this.loadCategories()
  },

  async loadCategories() {
    try {
      const res = await get('/category/list', { status: 1 })
      const cats = res.data || []
      this.setData({ categories: cats, currentCat: cats[0]?.id || 0 })
      if (cats[0]) this.loadProducts(cats[0].id)
    } catch (e) {}
  },

  selectCat(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ currentCat: id })
    this.loadProducts(id)
  },

  async loadProducts(categoryId) {
    try {
      const res = await get('/product/list', { category_id: categoryId, page: 1, page_size: 50 })
      // 用 wx.downloadFile 批量下载图片，真机才能渲染 <image>
      const products = await downloadImageFields(res.data?.list || [], 'image')
      this.setData({ products })
    } catch (e) {}
  },

  goDetail(e) {
    wx.navigateTo({ url: `/pages/detail/detail?id=${e.currentTarget.dataset.id}` })
  },
})
