/**
 * 最大使用量展示：纯数字时按 GB 2760 表 A.1 默认补全单位 g/kg，已有单位或非数值则原样返回。
 */
const UNIT_REG = /(g|mg)\/(kg|L|dm\s*\^?\s*2)|%|mL\/kg|以残留量计|残留量\s*[≤<]/i
const APPROPRIATE = /按生产需要适量使用|适量使用|gmp|proper level|as needed/i

export function formatMaxUsage(
  maxUsage: string | null | undefined,
  usageType?: string | null
): string {
  const s = (maxUsage ?? '').trim()
  if (!s) return '—'
  if (UNIT_REG.test(s)) return s
  if (APPROPRIATE.test(s)) return s
  if (/残留|residue/i.test(s)) return s
  // 纯数字且为最大使用量时补 g/kg
  if (/^\d+\.?\d*\s*$/.test(s) && (usageType === '最大使用量' || !usageType)) {
    return `${s} g/kg`
  }
  return s
}
