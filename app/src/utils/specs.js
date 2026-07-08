/**
 * 装备规格标签公共工具。
 * 抽取自 api/chat.js 与 api/product.js，消除两处完全重复的实现。
 */

const BALANCE_LABELS = {
  'head-heavy': '头重进攻',
  'head-light': '头轻速度',
  'even-balanced': '均衡控制',
}

const SHAFT_LABELS = {
  flexible: '中软杆',
  medium: '中杆适中',
  stiff: '中硬杆',
  'extra-stiff': '高硬杆',
}

const WIDTH_LABELS = {
  wide: '宽脚友好',
  'wide-friendly': '宽脚友好',
  regular: '标准鞋楦',
}

export function balanceLabel(value) {
  return BALANCE_LABELS[value] || String(value)
}

export function shaftLabel(value) {
  return SHAFT_LABELS[value] || String(value)
}

export function widthLabel(value) {
  return WIDTH_LABELS[value] || String(value)
}

/**
 * 从 specs 对象构造最多 4 条人类可读的规格标签。
 */
export function buildSpecList(specs) {
  if (!specs || typeof specs !== 'object') return []
  return [
    specs.weight_class && `${specs.weight_class} 重量`,
    specs.balance && balanceLabel(specs.balance),
    specs.shaft_flex && shaftLabel(specs.shaft_flex),
    specs.gauge && `线径 ${specs.gauge}`,
    specs.speed && `${specs.speed} 速`,
    specs.cushion_score && `缓震 ${specs.cushion_score}`,
    specs.support_score && `支撑 ${specs.support_score}`,
    specs.width_fit && widthLabel(specs.width_fit),
    specs.usage_scene && String(specs.usage_scene),
    specs.highlight && String(specs.highlight),
  ].filter(Boolean).slice(0, 4)
}
