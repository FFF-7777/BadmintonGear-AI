/**
 * 前端全局错误上报。
 *
 * 捕获 Vue 渲染异常、未处理 Promise rejection 和全局 error 事件。
 * 若配置了 VITE_ERROR_REPORT_URL 环境变量，则 POST 上报到该端点；
 * 否则仅输出到 console。生产环境可替换为 Sentry SDK。
 */

export function setupGlobalErrorHandler(app) {
  app.config.errorHandler = (err, _vm, info) => {
    console.error('[Vue Error]', err, info)
    reportError({ type: 'vue', message: String(err), info })
  }

  window.addEventListener('unhandledrejection', (event) => {
    console.error('[Unhandled Promise]', event.reason)
    reportError({ type: 'promise', message: String(event.reason) })
  })

  window.addEventListener('error', (event) => {
    console.error('[Global Error]', event.message)
    reportError({
      type: 'global',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
    })
  })
}

async function reportError(payload) {
  const url = import.meta.env?.VITE_ERROR_REPORT_URL
  if (!url) return
  try {
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        ts: Date.now(),
        ua: navigator.userAgent,
      }),
    })
  } catch {
    /* 上报失败静默，不影响用户 */
  }
}
