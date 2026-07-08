import { describe, it, expect } from 'vitest'
import { buildSpecList, balanceLabel, shaftLabel, widthLabel } from '../specs'

describe('balanceLabel', () => {
  it('maps known balance values', () => {
    expect(balanceLabel('head-heavy')).toBe('头重进攻')
    expect(balanceLabel('head-light')).toBe('头轻速度')
    expect(balanceLabel('even-balanced')).toBe('均衡控制')
  })

  it('passes through unknown values', () => {
    expect(balanceLabel('custom')).toBe('custom')
  })
})

describe('shaftLabel', () => {
  it('maps known shaft flex values', () => {
    expect(shaftLabel('flexible')).toBe('中软杆')
    expect(shaftLabel('medium')).toBe('中杆适中')
    expect(shaftLabel('stiff')).toBe('中硬杆')
    expect(shaftLabel('extra-stiff')).toBe('高硬杆')
  })
})

describe('widthLabel', () => {
  it('maps known width values', () => {
    expect(widthLabel('wide')).toBe('宽脚友好')
    expect(widthLabel('wide-friendly')).toBe('宽脚友好')
    expect(widthLabel('regular')).toBe('标准鞋楦')
  })
})

describe('buildSpecList', () => {
  it('builds spec list from racket specs', () => {
    const specs = {
      weight_class: '4U',
      balance: 'head-heavy',
      shaft_flex: 'medium',
    }
    const list = buildSpecList(specs)
    expect(list).toEqual(['4U 重量', '头重进攻', '中杆适中'])
  })

  it('returns empty for null input', () => {
    expect(buildSpecList(null)).toEqual([])
    expect(buildSpecList(undefined)).toEqual([])
  })

  it('returns empty for non-object input', () => {
    expect(buildSpecList('string')).toEqual([])
  })

  it('caps at 4 items', () => {
    const specs = {
      weight_class: '4U',
      balance: 'head-heavy',
      shaft_flex: 'medium',
      gauge: '0.68',
      speed: '77',
    }
    expect(buildSpecList(specs).length).toBe(4)
  })

  it('includes shoe specs', () => {
    const specs = {
      cushion_score: 9.2,
      support_score: 8.8,
      width_fit: 'wide',
    }
    const list = buildSpecList(specs)
    expect(list).toContain('缓震 9.2')
    expect(list).toContain('支撑 8.8')
    expect(list).toContain('宽脚友好')
  })
})
