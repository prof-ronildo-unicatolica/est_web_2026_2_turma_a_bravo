import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../services/api'

const cardsResumo = [
  { label: 'Hotéis ativos', value: '18', extra: '+3 neste mês', icon: '🏨', tone: 'primary' },
  { label: 'Cidades cadastradas', value: '12', extra: '2 novas', icon: '📍', tone: 'success' },
  { label: 'Usuários', value: '426', extra: '89 online', icon: '👥', tone: 'warning' },
  { label: 'Avaliações', value: '1.940', extra: '4,8/5 média', icon: '⭐', tone: 'info' }
]

const areasEmGestao = [
  { titulo: 'Gestão de hotéis', descricao: 'Revisão de unidades, preços e disponibilidade.', status: 'Em dia', destaque: '5 pendências' },
  { titulo: 'Cidades e destinos', descricao: 'Acompanhamento de alcance e campanhas regionais.', status: 'Ativa', destaque: '3 campanhas' },
  { titulo: 'Clientes e perfis', descricao: 'Controle de acessos, contas e alertas de segurança.', status: 'Monitorando', destaque: '12 alertas' }
]

const atividadesRecentes = [
  'Nova unidade cadastrada em Porto Alegre.',
  'Promoção de verão publicada para Florianópolis.',
  'Usuário administrador revisou reclamações do mês.',
  'Backup do sistema concluído com sucesso.'
]

export default function Admin() {
  const [usuario, setUsuario] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    async function carregarDadosAdmin() {
      try {
        const dados = await apiFetch('/auth/me')
        setUsuario(dados)
      } catch {
        setErro('Não foi possível carregar os dados do administrador.')
      }
    }

    carregarDadosAdmin()
  }, [])

  return (
    <div className="admin-panel">
      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
        <div>
          <span className="admin-badge">Painel administrativo</span>
          <h2 className="mb-1 mt-3">Bem-vindo ao console da rede</h2>
          <p className="mb-0 text-secondary">
            {usuario ? `Olá, ${usuario.nome}.` : 'Acompanhamento central da operação hoteleira.'}
          </p>
        </div>

        <Link to="/perfil" className="btn btn-primary btn-lg px-4">
          Ver perfil
        </Link>
      </div>

      {erro && (
        <div className="alert alert-warning" role="alert">
          {erro}
        </div>
      )}

      <div className="row g-3 mb-4">
        {cardsResumo.map((item) => (
          <div className="col-md-6 col-xl-3" key={item.label}>
            <div className={`stat-card stat-card-${item.tone}`}>
              <div className="stat-icon">{item.icon}</div>
              <div>
                <small>{item.label}</small>
                <h3>{item.value}</h3>
                <span>{item.extra}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="row g-4">
        <div className="col-lg-8">
          <div className="card shadow-sm admin-card h-100">
            <div className="card-body p-4">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h4 className="mb-0">Áreas em gestão</h4>
                <span className="text-muted small">Atualizado agora</span>
              </div>

              <div className="admin-list">
                {areasEmGestao.map((area) => (
                  <div className="admin-list-item" key={area.titulo}>
                    <div className="d-flex justify-content-between align-items-start gap-3">
                      <div>
                        <h5>{area.titulo}</h5>
                        <p>{area.descricao}</p>
                      </div>
                      <span className="admin-pill">{area.status}</span>
                    </div>
                    <small>{area.destaque}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="col-lg-4">
          <div className="card shadow-sm admin-card mb-4">
            <div className="card-body p-4">
              <h4 className="mb-3">Atalhos rápidos</h4>
              <div className="d-grid gap-2">
                <Link to="/hoteis" className="btn btn-outline-primary text-start">
                  Gerenciar hotéis
                </Link>
                <Link to="/cidades" className="btn btn-outline-success text-start">
                  Revisar cidades
                </Link>
                <Link to="/perfil" className="btn btn-outline-secondary text-start">
                  Ver usuários e perfil
                </Link>
              </div>
            </div>
          </div>

          <div className="card shadow-sm admin-card">
            <div className="card-body p-4">
              <h4 className="mb-3">Atividades recentes</h4>
              <ul className="activity-list">
                {atividadesRecentes.map((atividade) => (
                  <li key={atividade}>{atividade}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}