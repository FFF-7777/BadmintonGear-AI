/**
 * 图片加载工具（真机兼容）
 *
 * 微信小程序真机上 <image src="http://..."> 会被安全策略拦截，
 * 即使 project.config.json 设了 urlCheck:false 也绕不过。
 * 解决方案：用 wx.downloadFile 将 http 图片下载到本地临时文件，
 * 再用临时文件路径渲染 <image>。
 */
const { FILE_BASE_URL } = require('./request')

/** 已下载图片缓存 {url: tempFilePath}，避免重复下载 */
const _cache = {}

/**
 * 下载单张图片，返回可用的 <image src> 路径
 * - 真机环境：返回临时文件路径 (wxfile://...)
 * - 模拟器/下载失败：降级返回原 URL（模拟器能直接显示 http 图片）
 *
 * @param {string} url - 完整或相对图片路径
 * @returns {Promise<string>} 可用于 <image src> 的路径
 */
function downloadImage(url) {
  if (!url) return Promise.resolve('')

  // 已经是完整 URL
  const fullUrl = /^https?:\/\//.test(url) ? url : FILE_BASE_URL + (url.startsWith('/') ? url : `/${url}`)

  // 命中缓存直接返回
  if (_cache[fullUrl]) return Promise.resolve(_cache[fullUrl])

  return new Promise((resolve) => {
    wx.downloadFile({
      url: fullUrl,
      success(res) {
        if (res.statusCode === 200 && res.tempFilePath) {
          _cache[fullUrl] = res.tempFilePath
          resolve(res.tempFilePath)
        } else {
          // 下载失败降级返回原 URL（模拟器上仍可用）
          resolve(fullUrl)
        }
      },
      fail() {
        // 下载失败降级
        resolve(fullUrl)
      },
    })
  })
}

/**
 * 批量下载列表中每个对象的指定图片字段
 * @param {Array} list - 对象数组
 * @param {string} imageKey - 图片字段名（如 'image'、'product_image'）
 * @param {string} [urlKey] - 如果源数据存的是相对路径且需先拼接，指定该字段名；默认同 imageKey
 * @returns {Promise<Array>} 新列表（每个对象的 imageKey 已替换为本地路径）
 */
async function downloadImageFields(list, imageKey, urlKey) {
  const key = urlKey || imageKey
  if (!list || !list.length) return []
  const tasks = list.map(async (item) => {
    const localPath = await downloadImage(item[key])
    return { ...item, [imageKey]: localPath }
  })
  return Promise.all(tasks)
}

/**
 * 下载单张图片并返回路径（用于头像等单独场景）
 * @param {string} url - 图片路径
 * @returns {Promise<string>}
 */
async function resolveImage(url) {
  return downloadImage(url)
}

module.exports = { downloadImage, downloadImageFields, resolveImage, _cache }
