import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

export interface Additive {
  faid: number
  nameCn: string
  nameEn: string | null
  cns: string | null
  ins: string | null
  function: string | null
}

export interface UsageItem {
  foodCategoryCode: string
  foodName: string
  maxUsage: string
  remark: string | null
  usageType: string | null
  residueNote: string | null
}

export interface AdditiveDetail extends Additive {
  usage: UsageItem[]
}

export interface Category {
  categoryCode: string
  categoryName: string
  limitId: number | null
}

export interface CategoryAdditive {
  faid: number
  nameCn: string
  nameEn: string | null
  cns: string | null
  ins: string | null
  function: string | null
  maxUsage: string
  remark: string | null
  usageType: string | null
  residueNote: string | null
  /** 本级/上级/GMP：direct=本级, parent=继承自父级, gmp=适量使用 */
  source?: string | null
  /** 单位，如 g/kg */
  unit?: string | null
}

export interface CategoryDetail extends Category {
  additives: CategoryAdditive[]
  /** 本级允许使用的添加剂（直接规定在该分类下） */
  directAdditives?: CategoryAdditive[]
  /** 继承自父级分类允许使用的添加剂 */
  parentAdditives?: CategoryAdditive[]
  /** 按生产需要适量使用的添加剂（表 A.2） */
  gmpAdditives?: CategoryAdditive[]
}

export const api = {
  getAdditives: (q?: string) =>
    client.get<Additive[]>('/additives', { params: q ? { q } : {} }).then((r) => r.data),
  getAdditive: (faid: number) =>
    client.get<AdditiveDetail>(`/additives/${faid}`).then((r) => r.data),
  getCategories: (q?: string) =>
    client.get<Category[]>('/categories', { params: q ? { q } : {} }).then((r) => r.data),
  getCategory: (code: string) =>
    client.get<CategoryDetail>(`/categories/${encodeURIComponent(code)}`).then((r) => r.data),
  getProcessingAids: () => client.get<Record<string, unknown>[]>('/reference/processing-aids').then((r) => r.data),
  getEnzymes: () => client.get<Record<string, unknown>[]>('/reference/enzymes').then((r) => r.data),
  getSpicesB1: () => client.get<Record<string, unknown>[]>('/reference/spices/b1').then((r) => r.data),
  getSpicesB2: () => client.get<Record<string, unknown>[]>('/reference/spices/b2').then((r) => r.data),
  getSpicesB3: () => client.get<Record<string, unknown>[]>('/reference/spices/b3').then((r) => r.data),
  getAppendixD: () => client.get<Record<string, unknown>[]>('/reference/appendix-d').then((r) => r.data),
  getSiteRules: () => client.get<Record<string, unknown>>('/reference/site-rules').then((r) => r.data),
  getSpicesRules: () => client.get<Record<string, unknown>>('/reference/spices-rules').then((r) => r.data),
}
