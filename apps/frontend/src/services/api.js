const baseURL = 'http://localhost:8000/api/v1'

async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem('token')

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${baseURL}${endpoint}`, {
    ...options,
    headers
  })

  if (response.status === 401) {
    localStorage.removeItem('token')
    throw new Error('401')
  }

  if (!response.ok) {
    // Tenta ler a mensagem que o backend enviou (campo "detail").
    let mensagem = ''
    try {
      const corpo = await response.json()
      if (typeof corpo.detail === 'string') {
        mensagem = corpo.detail
      } else if (Array.isArray(corpo.detail)) {
        mensagem = corpo.detail.map((item) => item.msg).join('; ')
      }
    } catch {
      // resposta sem JSON: usa a mensagem padrao abaixo
    }

    const erro = new Error(mensagem || `Erro na API: ${response.status}`)
    erro.status = response.status
    throw erro
  }

  return response.json()
}

export { baseURL, apiFetch }