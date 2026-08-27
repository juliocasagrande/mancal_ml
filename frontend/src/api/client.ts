const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
  } catch {
    // corpo não é JSON — não expõe o texto bruto (Seção 17 do blueprint)
  }
  return 'Não foi possível completar a solicitação.'
}

export async function apiGet<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(path, BASE_URL)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value))
    }
  }

  let response: Response
  try {
    response = await fetch(url.toString())
  } catch {
    throw new ApiError(0, 'Não foi possível conectar à API.')
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response))
  }
  return response.json() as Promise<T>
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch(new URL(path, BASE_URL).toString(), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'Não foi possível conectar à API.')
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response))
  }
  return response.json() as Promise<T>
}
