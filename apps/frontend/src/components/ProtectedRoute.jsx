import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { apiFetch } from '../services/api'

export default function ProtectedRoute({ children, adminOnly = false }) {
  const [usuario, setUsuario] = useState(null)
  const [carregando, setCarregando] = useState(true)

  const token = localStorage.getItem('token')

  useEffect(() => {
    async function verificarUsuario() {
      if (!token) {
        setCarregando(false)
        return
      }

      try {
        const dados = await apiFetch('/auth/me')
        setUsuario(dados)
      } catch (erro) {
        setUsuario(null)
      } finally {
        setCarregando(false)
      }
    }

    verificarUsuario()
  }, [token])

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (carregando) {
    return (
      <div className="alert alert-info">
        Verificando acesso...
      </div>
    )
  }

  if (!usuario) {
    return <Navigate to="/login" replace />
  }

  if (adminOnly && !usuario.is_admin) {
    return (
      <div className="alert alert-danger">
        Acesso restrito a administradores.
      </div>
    )
  }

  return children
}