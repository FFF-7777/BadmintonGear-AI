/**
 * 网络请求封装
 * 统一处理Token和响应
 */
// 本地调试地址说明：
// - 开发者工具「模拟器」用 127.0.0.1 即可（小程序运行在本机，能连到本机后端，且不受 DHCP 换 IP 影响）
// - 「真机调试 / 预览」必须改成电脑当前的局域网 IP，例如 http://10.242.53.32:8000/api
//   （手机上的 127.0.0.1 指向手机自己，连不到电脑上的后端；局域网 IP 由 DHCP 分配，重连 WiFi 可能变化）
// - 查看当前 IP：PowerShell 执行 Get-NetIPAddress -AddressFamily IPv4
// - 注意：若开着 Clash Verge(Mihomo) TUN 模式做真机调试，需确保其规则对局域网段(10.*/192.168.*)为 DIRECT，否则会被代理拦截
// - project.config.json 已设 urlCheck:false，开发者工具不校验域名/HTTPS，故本地 HTTP 也能跑
const BASE_URL = 'http://10.242.53.32:8000/api'
/** 静态资源根地址（图片等，不含 /api） */
const FILE_BASE_URL = BASE_URL.replace(/\/api$/, '')

/**
 * 发起HTTP请求
 * @param {Object} options - 请求配置
 * @returns {Promise} 请求结果
 */
function request(options) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token') || ''
    wx.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header,
      },
      success(res) {
        if (res.data.code === 200) {
          resolve(res.data)
        } else if (res.data.code === 401) {
          wx.removeStorageSync('token')
          wx.redirectTo({ url: '/pages/login/login' })
          reject(res.data)
        } else {
          wx.showToast({ title: res.data.msg || '请求失败', icon: 'none' })
          reject(res.data)
        }
      },
      fail(err) {
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
    })
  })
}

/** GET请求 */
function get(url, data) {
  return request({ url, method: 'GET', data })
}

/** POST请求 */
function post(url, data) {
  return request({ url, method: 'POST', data })
}

/** PUT请求 */
function put(url, data) {
  return request({ url, method: 'PUT', data })
}

/** DELETE请求 */
function del(url, data) {
  return request({ url, method: 'DELETE', data })
}

/**
 * 上传文件
 * @param {string} url - 接口路径
 * @param {string} filePath - 本地临时文件路径
 * @returns {Promise} 上传结果
 */
function uploadFile(url, filePath) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token') || ''
    wx.uploadFile({
      url: BASE_URL + url,
      filePath,
      name: 'file',
      header: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      success(res) {
        let data = {}
        try {
          data = JSON.parse(res.data)
        } catch (e) {
          wx.showToast({ title: '上传失败', icon: 'none' })
          reject(e)
          return
        }
        if (data.code === 200) {
          resolve(data)
        } else if (data.code === 401) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('userInfo')
          wx.redirectTo({ url: '/pages/login/login' })
          reject(data)
        } else {
          wx.showToast({ title: data.msg || '上传失败', icon: 'none' })
          reject(data)
        }
      },
      fail(err) {
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
    })
  })
}

/** 拼接完整图片地址 */
function resolveImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return FILE_BASE_URL + url
}

module.exports = { request, get, post, put, del, uploadFile, resolveImageUrl, BASE_URL, FILE_BASE_URL }
