import { describe, expect, it } from 'vitest'
import { parseMarkdown } from '../markdown'

describe('parseMarkdown', () => {
  it('escapes raw HTML before rendering markdown', () => {
    const html = parseMarkdown('<img src=x onerror="alert(1)"> **安全**')

    expect(html).toContain('&lt;img')
    expect(html).not.toContain('<img')
    expect(html).toContain('<strong>安全</strong>')
  })
})
