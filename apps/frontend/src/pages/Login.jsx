import { useState } from 'react'
import { apiFetch } from '../services/api'

export default function Login() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()

    try {
      const resposta = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email,
          senha
        })
      })

      localStorage.setItem('token', resposta.access_token)

      alert('Login realizado com sucesso')
    } catch (erro) {
      alert('E-mail ou senha incorretos')
    }
  }

  return (
    <div className="card shadow-sm">
      <div className="card-body p-4">
        <h2 className="mb-4">Login</h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">E-mail</label>
            <input
              type="email"
              className="form-control"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Senha</label>
            <input
              type="password"
              className="form-control"
              value={senha}
              onChange={(event) => setSenha(event.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary">
            Entrar
          </button>
        </form>
      </div>
    </div>
  )
}