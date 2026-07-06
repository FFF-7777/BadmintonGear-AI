/**
 * 轻量级 Markdown → HTML 解析器
 * 专为微信小程序 <rich-text> 组件设计
 *
 * 支持语法：
 *   **加粗** / __加粗__  →  <strong>加粗</strong>
 *   *斜体* / _斜体_       →  <em>斜体</em>
 *   `行内代码`             →  <code>行内代码</code>
 *   - 无序列表项           →  <ul><li>...</li></ul>
 *   # ## ### 标题           →  <h1>/<h2>/<h3>
 *   > 引用                  →  <blockquote>
 *   空行分段                →  <p>
 *
 * @param {string} md - Markdown 原始文本
 * @returns {string} HTML 字符串
 */
function parseMarkdown(md) {
  if (!md) return ''

  // 预处理：标准化换行符，去除首尾空白
  let html = md.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim()

  // ===== 1. 转义 HTML 特殊字符（在解析 MD 之前保护已有实体）=====
  html = escapeHtml(html)

  // ===== 2. 代码块（```...```）- 先处理防止内部被转义 =====
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return '<pre><code class="lang-' + (lang || '') + '">' + code.trim() + '</code></pre>'
  })

  // ===== 3. 行内代码 `code` =====
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>')

  // ===== 4. 标题 # ~ ###### =====
  html = html.replace(/^###### (.+)$/gm, '<h6>$1</h6>')
  html = html.replace(/##### (.+)$/gm, '<h5>$1</h5>')
  html = html.replace(/#### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // ===== 5. 加粗 **text** 和 __text__（放在斜体前）======
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>')

  // ===== 6. 斜体 *text* 和 _text_（排除已处理的 **）======
  html = html.replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
  html = html.replace(/_([^_\n]+)_/g, '<em>$1</em>')

  // ===== 7. 引用块 > text =====
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>')

  // ===== 8. 无序列表 - item 或 * item =====
  const listItems = []
  html = html.replace(/^[-*] (.+)$/gm, (match, content) => {
    listItems.push('<li>' + content + '</li>')
    return '' // 占位替换
  })
  // 合并连续的列表项为 <ul>
  if (listItems.length > 0) {
    html = html.replace(/(\n\s*){2,}/g, '\n') // 压缩多余空行
    const ulHtml = '<ul class="md-list">' + listItems.join('') + '</ul>'
    html += '\n' + ulHtml
  }

  // ===== 9. 分段处理（空行分隔 → <p> 段落）======
  const lines = html.split('\n')
  const paragraphs = []
  let currentPara = ''

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    // 已是块级标签的单独一行不包裹 p
    if (/^<(h[1-6]|pre|ul|ol|blockquote|table)/.test(line)) {
      if (currentPara) {
        paragraphs.push(wrapParagraph(currentPara))
        currentPara = ''
      }
      paragraphs.push(line)
    } else if (line === '') {
      // 空行：结束当前段落
      if (currentPara) {
        paragraphs.push(wrapParagraph(currentPara))
        currentPara = ''
      }
    } else {
      currentPara += (currentPara ? '<br/>' : '') + line
    }
  }
  if (currentPara) {
    paragraphs.push(wrapParagraph(currentPara))
  }

  return paragraphs.join('')
}

/** 将文本包裹为段落 */
function wrapParagraph(content) {
  // 如果内容已经是块级 HTML，直接返回
  if (/^<(h[1-6]|pre|ul|ol|blockquote|p|div)/.test(content)) return content
  return '<p>' + content + '</p>'
}

/** 转义 HTML 特殊字符 */
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

module.exports = { parseMarkdown }
