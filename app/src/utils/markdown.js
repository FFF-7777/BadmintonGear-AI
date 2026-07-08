/**
 * 轻量级 Markdown → HTML 解析器（移植自原小程序 utils/markdown.js）
 * 支持：标题/加粗/斜体/行内代码/代码块/无序列表/引用/分段
 * 注意：已转义 HTML 特殊字符，配合 v-html 使用（内容来自内部可信 AI 源）。
 */
export function parseMarkdown(md) {
  if (!md) return ''

  let html = md.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim()
  html = escapeHtml(html)

  // 代码块 ```...```
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return '<pre><code class="lang-' + (lang || '') + '">' + code.trim() + '</code></pre>'
  })

  // 行内代码
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>')

  // 标题
  html = html.replace(/^###### (.+)$/gm, '<h6>$1</h6>')
  html = html.replace(/##### (.+)$/gm, '<h5>$1</h5>')
  html = html.replace(/#### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // 加粗
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>')

  // 斜体
  html = html.replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
  html = html.replace(/_([^_\n]+)_/g, '<em>$1</em>')

  // 引用
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>')

  // 无序列表
  const listItems = []
  html = html.replace(/^[-*] (.+)$/gm, (match, content) => {
    listItems.push('<li>' + content + '</li>')
    return ''
  })
  if (listItems.length > 0) {
    html = html.replace(/(\n\s*){2,}/g, '\n')
    const ulHtml = '<ul class="md-list">' + listItems.join('') + '</ul>'
    html += '\n' + ulHtml
  }

  // 分段
  const lines = html.split('\n')
  const paragraphs = []
  let currentPara = ''
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (/^<(h[1-6]|pre|ul|ol|blockquote|table)/.test(line)) {
      if (currentPara) {
        paragraphs.push(wrapParagraph(currentPara))
        currentPara = ''
      }
      paragraphs.push(line)
    } else if (line === '') {
      if (currentPara) {
        paragraphs.push(wrapParagraph(currentPara))
        currentPara = ''
      }
    } else {
      currentPara += (currentPara ? '<br/>' : '') + line
    }
  }
  if (currentPara) paragraphs.push(wrapParagraph(currentPara))

  return paragraphs.join('')
}

function wrapParagraph(content) {
  if (/^<(h[1-6]|pre|ul|ol|blockquote|p|div)/.test(content)) return content
  return '<p>' + content + '</p>'
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
