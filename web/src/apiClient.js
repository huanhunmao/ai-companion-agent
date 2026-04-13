/**
 * 生产环境建议留空 VITE_API_BASE_URL，由 Nginx 等同源反代 /api；
 * 本地开发使用 Vite proxy，同样留空即可。
 * 若前后端分域部署，设为完整后端 origin，例如 https://api.example.com
 */
const rawBase = (import.meta.env.VITE_API_BASE_URL ?? '').trim().replace(/\/$/, '')

export function getApiBaseUrl() {
  return rawBase
}

export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${rawBase}${p}`
}

export function getApiHeaders(extra = {}) {
  const headers = { ...extra }
  const key = (import.meta.env.VITE_APP_API_KEY ?? '').trim()
  if (key) {
    headers.Authorization = `Bearer ${key}`
  }
  return headers
}
