import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'

export default function Cadastro() {
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(event) {
    event.preventDefault()

    setErro('')
    setSucesso('')

    try {
      await apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          nome,
          email,
          senha
        })
      })

      setSucesso('Cadastro realizado com sucesso!')

      setTimeout(() => {
        navigate('/login')
      }, 1500)
    } catch (erro) {
      setErro('Não foi possível realizar o cadastro.')
    }
  }

  return (
    <div className="card shadow-sm">
      <div className="card-body p-4">
        <h2 className="mb-4">Cadastro</h2>

        {erro && (
          <div className="alert alert-danger">
            {erro}
          </div>
        )}

        {sucesso && (
          <div className="alert alert-success">
            {sucesso}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Nome</label>
            <input
              type="text"
              className="form-control"
              value={nome}
              onChange={(event) => setNome(event.target.value)}
              required
            />
          </div>

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
              minLength="6"
              required
            />
          </div>

          <button type="submit" className="btn btn-primary">
            Cadastrar
          </button>
        </form>
      </div>
    </div>
  )
}