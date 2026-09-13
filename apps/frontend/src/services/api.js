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

  if (!response.ok) {
    throw new Error(`Erro na API: ${response.status}`)
  }

  return response.json()
}

export { baseURL, apiFetch }