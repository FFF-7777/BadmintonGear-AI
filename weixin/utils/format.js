/**
 * 日期格式化工具
 * 日期格式: 2026-11-02
 * 日期时间格式: 2026-11-02 17:25:17
 */
const { FILE_BASE_URL } = require('./request')

/**
 * 将相对路径转为完整图片 URL（小程序 image 组件需 http 完整地址）
 * @param {string} url - 图片路径
 * @returns {string} 完整 URL
 */
function formatImageUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  return FILE_BASE_URL + (url.startsWith('/') ? url : `/${url}`)
}

/**
 * 格式化日期时间
 * @param {string|Date} dateStr - 日期字符串
 * @returns {string} 格式化后的日期时间
 */
function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}:${s}`
}

/** 订单状态映射 */
const orderStatusMap = {
  0: '待支付', 1: '已支付', 2: '已发货', 3: '已完成', 4: '已取消',
}

module.exports = { formatDateTime, orderStatusMap, formatImageUrl }
