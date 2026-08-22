const baseURL = 'http://localhost:8000/api/v1'

async function apiFetch(endpoint, options = {}) {
  const response = await fetch(`${baseURL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  })

  if (!response.ok) {
    throw new Error(`Erro na API: ${response.status}`)
  }

  return response.json()
}

export { baseURL, apiFetch }
