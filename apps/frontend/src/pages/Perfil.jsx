import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'

export default function Perfil() {
  const [usuario, setUsuario] = useState(null)
  const [erro, setErro] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    async function carregarPerfil() {
      const token = localStorage.getItem('token')

      if (!token) {
        navigate('/login')
        retunr
      }
      
      try {
        const dados = await apiFetch('/auth/me')
        setUsuario(dados)
      } catch (erro) {
        if (erro.message === '401') {
          navigate('/login')
          return
        }

        setErro('Não foi possível carregar o perfil')
      }
    }

    carregarPerfil()
  }, [navigate])

  if (erro) {
    return (
      <div className="alert alert-danger">
        {erro}
      </div>
    )
  }

  if (!usuario) {
    return (
      <div className="alert alert-info">
        Carregando perfil...
      </div>
    )
  }

  return (
    <div className="card shadow-sm">
      <div className="card-body p-4">
        <h2 className="mb-4">Perfil</h2>

        <p>
          <strong>Nome:</strong> {usuario.nome}
        </p>

        <p>
          <strong>E-mail:</strong> {usuario.email}
        </p>

        <p>
          <strong>Tipo de usuário:</strong>{' '}
          {usuario.is_admin ? 'Administrador' : 'Cliente'}
        </p>
      </div>
    </div>
  )
}