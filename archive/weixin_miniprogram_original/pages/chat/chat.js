/**
 * AI智能客服对话页面
 * 基于 LangChain RAG 增强检索（羽毛球装备智能导购）
 * 使用 WebSocket 流式输出 + Markdown 渲染 + 流式节流滚动优化
 */
const { BASE_URL } = require('../../utils/request')
const { formatDateTime } = require('../../utils/format')
const { parseMarkdown } = require('../../utils/markdown')

// 将 http 协议的 BASE_URL 转换为 ws/wss
function getWsUrl() {
  const url = BASE_URL.replace(/^http/, 'ws')
  return url + '/chat/ws'
}

/** 流式刷新节流间隔（ms），平衡流畅度与渲染性能 */
const STREAM_THROTTLE_MS = 150

Page({
  data: {
    messages: [],
    inputText: '',
    sessionId: '',
    loading: false,
    /** scroll-top 递增值，每次 ++ 触发滚到底部 */
    scrollTop: 0,
    socketConnected: false, // WebSocket 连接状态
  },

  /** ===== 流式缓冲区（非渲染数据）===== */
  _streamBuffer: '',      // 累积的原始文本片段
  _streamTimer: null,     // 节流定时器
  _scrollCounter: 0,      // scrollTop 递增计数器

  onLoad() {
    if (!wx.getStorageSync('token')) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    // 欢迎消息（纯文本，不需要MD解析）
    this.setData({
      messages: [{
        id: 0, role: 'assistant',
        content: '您好！我是羽毛球装备智能导购AI客服，有什么可以帮您的吗？',
        time: formatDateTime(new Date()),
        htmlContent: '<p>您好！我是羽毛球装备智能导购AI客服，有什么可以帮您的吗？</p>',
      }],
    })
    this.connectWebSocket()
  },

  onUnload() {
    // 页面卸载时关闭 WebSocket 并清理定时器
    this._clearStreamTimer()
    this.closeSocket()
  },

  onInput(e) { this.setData({ inputText: e.detail.value }) },

  /** 清理流式节流定时器 */
  _clearStreamTimer() {
    if (this._streamTimer) {
      clearTimeout(this._streamTimer)
      this._streamTimer = null
    }
  },

  /** 刷新缓冲区内容到视图 + 滚动到底部 */
  _flushStreamToView() {
    this._streamTimer = null
    const buffer = this._streamBuffer
    if (!buffer) return
    // 清空缓冲区
    this._streamBuffer = ''

    const msgs = this.data.messages
    if (msgs.length === 0 || msgs[msgs.length - 1].role !== 'assistant') return

    const lastMsg = msgs[msgs.length - 1]
    const newContent = (lastMsg._rawContent || lastMsg.content) + buffer
    lastMsg._rawContent = newContent
    lastMsg.htmlContent = parseMarkdown(newContent)
    lastMsg.content = newContent

    // scrollTop 递增 → 必触发滚动（解决 scroll-into-view 相同值不重复触发的问题）
    this._scrollCounter++
    this.setData({
      messages: [...msgs],
      scrollTop: this._scrollCounter,
    })
  },

  /**
   * 追加流式内容片段（带节流）
   * 文本先写入缓冲区，按 STREAM_THROTTLE_MS 批量刷新到视图，
   * 避免高频 setData 锁死 scroll-view 的手势响应。
   */
  appendStreamContent(content) {
    const msgs = this.data.messages
    if (msgs.length === 0 || msgs[msgs.length - 1].role !== 'assistant') return

    // 追加到缓冲区
    this._streamBuffer += content

    // 节流：已有定时器则等待合并刷新，否则启动新的定时器
    if (this._streamTimer) return

    this._streamTimer = setTimeout(() => {
      this._flushStreamToView()
    }, STREAM_THROTTLE_MS)
  },

  /** 强制立即刷新剩余缓冲区（用于 done / error 等需要即时展示的场景） */
  _flushStreamImmediate() {
    this._clearStreamTimer()
    this._flushStreamToView()
  },

  /** 建立 WebSocket 连接 */
  connectWebSocket() {
    if (this.socketConnecting || this.data.socketConnected) return

    const token = wx.getStorageSync('token') || ''
    const wsUrl = getWsUrl() + '?token=' + encodeURIComponent(token)
    this.socketConnecting = true

    const socketTask = wx.connectSocket({
      url: wsUrl,
      fail: (err) => {
        this.socketConnecting = false
        console.error('WebSocket 连接失败:', err)
      },
    })
    this.socketTask = socketTask

    socketTask.onOpen(() => {
      console.log('WebSocket 已连接')
      this.socketConnecting = false
      this.setData({ socketConnected: true })
    })

    socketTask.onMessage((res) => {
      try {
        const msg = JSON.parse(res.data)
        this.handleSocketMessage(msg)
      } catch (e) {
        console.error('解析消息失败:', e, res.data)
      }
    })

    socketTask.onError((err) => {
      console.error('WebSocket 错误:', err)
      this.socketConnecting = false
      this.setData({ socketConnected: false })
    })

    socketTask.onClose(() => {
      console.log('WebSocket 已关闭')
      this.socketConnecting = false
      this.socketTask = null
      this.setData({ socketConnected: false })
    })
  },

  /** 关闭 WebSocket */
  closeSocket() {
    if (this.socketTask) {
      try { this.socketTask.close() } catch (e) {}
    }
    this.socketTask = null
    this.socketConnecting = false
    this.setData({ socketConnected: false })
  },

  /** 处理服务端推送的消息 */
  handleSocketMessage(msg) {
    switch (msg.type) {
      case 'session_id':
        // 收到会话ID
        this.setData({ sessionId: msg.session_id })
        break

      case 'content':
        // 流式内容片段 - 追加到最后一条 assistant 消息（带节流）
        this.appendStreamContent(msg.content)
        break

      case 'sources':
        // 先刷新缓冲区，再挂载来源
        this._flushStreamImmediate()
        this.attachSources(msg.sources || [])
        break

      case 'done':
        // 流式结束 - 强制刷新缓冲区并标记加载完成
        this._flushStreamImmediate()
        this.finalizeStream(msg.answer)
        break

      case 'error':
        // 错误信息 - 强制刷新后展示错误
        this._flushStreamImmediate()
        this.handleStreamError(msg.message)
        break
    }
  },

  /** 将检索来源附加到当前AI回复 */
  attachSources(sources) {
    const msgs = this.data.messages
    if (msgs.length === 0 || msgs[msgs.length - 1].role !== 'assistant') return
    msgs[msgs.length - 1].sources = sources
    this.setData({ messages: [...msgs] })
  },

  /** 完成流式输出 */
  finalizeStream(answer) {
    this.setData({
      loading: false,
    })
    // 最终答案确保渲染完整
    const msgs = this.data.messages
    if (msgs.length > 0 && msgs[msgs.length - 1].role === 'assistant') {
      const lastMsg = msgs[msgs.length - 1]
      lastMsg._rawContent = answer
      lastMsg.content = answer
      lastMsg.htmlContent = parseMarkdown(answer)
      // 最终也递增一次 scrollTop 确保到底
      this._scrollCounter++
      this.setData({ messages: [...msgs], scrollTop: this._scrollCounter })
    }
  },

  /** 处理流式错误 */
  handleStreamError(message) {
    const errMsg = message || 'AI 服务异常'
    const msgs = this.data.messages
    const errorContent = `[错误] ${errMsg}`
    const lastMsg = msgs[msgs.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && this.data.loading) {
      lastMsg.content = errorContent
      lastMsg._rawContent = errorContent
      lastMsg.htmlContent = parseMarkdown(errorContent)
    } else {
      msgs.push({
        id: Date.now(),
        role: 'assistant',
        content: errorContent,
        htmlContent: parseMarkdown(errorContent),
        time: formatDateTime(new Date()),
      })
    }
    this._scrollCounter++
    this.setData({
      messages: [...msgs],
      loading: false,
      scrollTop: this._scrollCounter,
    })
  },

  /** 发送消息给 AI 客服 */
  sendMessage() {
    const text = this.data.inputText.trim()
    if (!text || this.data.loading) return

    // 如果 WebSocket 未连接，尝试重连
    if (!this.data.socketConnected) {
      wx.showToast({ title: '正在连接...', icon: 'none' })
      this.connectWebSocket()
      return
    }

    // 用户消息
    const userMsg = {
      id: Date.now(), role: 'user', content: text,
      time: formatDateTime(new Date()),
    }

    // 占位的 AI 回复消息（流式填充）
    const aiPlaceholder = {
      id: Date.now() + 1, role: 'assistant',
      content: '', _rawContent: '', htmlContent: '<p class="streaming-cursor">思考中...</p>',
      time: formatDateTime(new Date()),
    }

    const newMessages = [...this.data.messages, userMsg, aiPlaceholder]
    this._scrollCounter++
    this.setData({
      messages: newMessages,
      inputText: '',
      loading: true,
      scrollTop: this._scrollCounter,
    })

    // 重置缓冲区（新的一轮流式开始）
    this._streamBuffer = ''
    this._clearStreamTimer()

    // 通过 WebSocket 发送消息
    const sendData = JSON.stringify({
      message: text,
      session_id: this.data.sessionId || undefined,
    })

    this.socketTask.send({
      data: sendData,
      fail: (err) => {
        console.error('发送失败:', err)
        this.handleStreamError('消息发送失败，请检查网络连接')
      }
    })
  },
})
