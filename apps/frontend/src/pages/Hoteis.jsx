import { useEffect, useState } from 'react'
import { apiFetch } from '../services/api'

const estadoInicial = {
  nome: '',
  cidade_id: '',
  endereco: '',
  estrelas: 3,
  status: 'Ativo',
  diaria: 'R$ 0'
}

export default function Hoteis() {
  const [hoteis, setHoteis] = useState([])
  const [cidades, setCidades] = useState([])
  const [form, setForm] = useState(estadoInicial)
  const [editandoId, setEditandoId] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')

  async function carregarDados() {
    try {
      setErro('')
      const [listaHoteis, listaCidades] = await Promise.all([
        apiFetch('/hoteis'),
        apiFetch('/cidades')
      ])

      setHoteis(listaHoteis)
      setCidades(listaCidades)
    } catch {
      setErro('Não foi possível carregar hotéis e cidades.')
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarDados()
  }, [])

  function handleChange(event) {
    const { name, value } = event.target
    setForm((atual) => ({ ...atual, [name]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()

    if (!form.nome.trim() || !form.cidade_id || !form.endereco.trim()) {
      alert('Informe o nome do hotel, a cidade e o endereço.')
      return
    }

    try {
      const payload = {
        nome: form.nome.trim(),
        cidade_id: form.cidade_id,
        endereco: form.endereco.trim(),
        estrelas: Number(form.estrelas),
        status: form.status,
        diaria: form.diaria
      }

      if (editandoId !== null) {
        await apiFetch(`/hoteis/${editandoId}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        })
      } else {
        await apiFetch('/hoteis', {
          method: 'POST',
          body: JSON.stringify(payload)
        })
      }

      await carregarDados()
      setEditandoId(null)
      setForm(estadoInicial)
    } catch {
      alert('Não foi possível salvar o hotel.')
    }
  }

  function handleEditar(hotel) {
    setEditandoId(hotel.id)
    setForm({
      nome: hotel.nome,
      cidade_id: hotel.cidade_id,
      endereco: hotel.endereco,
      estrelas: hotel.estrelas,
      status: hotel.status,
      diaria: hotel.diaria
    })
  }

  async function handleExcluir(id) {
    try {
      await apiFetch(`/hoteis/${id}`, { method: 'DELETE' })
      await carregarDados()

      if (editandoId === id) {
        setEditandoId(null)
        setForm(estadoInicial)
      }
    } catch {
      alert('Não foi possível excluir o hotel.')
    }
  }

  function handleCancelar() {
    setEditandoId(null)
    setForm(estadoInicial)
  }

  return (
    <div className="admin-panel">
      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
        <div>
          <span className="admin-badge">Gestão de hotéis</span>
          <h2 className="mb-1 mt-3">Hotéis da rede</h2>
          <p className="mb-0 text-secondary">
            Cadastre, edite e acompanhe a operação dos hotéis vinculados.
          </p>
        </div>
      </div>

      {erro && (
        <div className="alert alert-warning">{erro}</div>
      )}

      <div className="row g-4 align-items-start">
        <div className="col-lg-4">
          <div className="card shadow-sm admin-card h-100">
            <div className="card-body p-4">
              <h4 className="mb-3">{editandoId !== null ? 'Editar hotel' : 'Novo hotel'}</h4>

              <form onSubmit={handleSubmit} className="city-form">
                <div className="mb-3">
                  <label className="form-label">Nome do hotel</label>
                  <input
                    type="text"
                    className="form-control"
                    name="nome"
                    value={form.nome}
                    onChange={handleChange}
                    placeholder="Ex.: Hotel Mar e Sol"
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Cidade</label>
                  <select
                    className="form-select"
                    name="cidade_id"
                    value={form.cidade_id}
                    onChange={handleChange}
                  >
                    <option value="">Selecione a cidade</option>
                    {cidades.map((cidade) => (
                      <option key={cidade.id} value={cidade.id}>{cidade.nome}</option>
                    ))}
                  </select>
                </div>

                <div className="mb-3">
                  <label className="form-label">Endereço</label>
                  <input
                    type="text"
                    className="form-control"
                    name="endereco"
                    value={form.endereco}
                    onChange={handleChange}
                    placeholder="Ex.: Rua das Flores, 123"
                  />
                </div>

                <div className="row g-2">
                  <div className="col-6">
                    <div className="mb-3">
                      <label className="form-label">Estrelas</label>
                      <select
                        className="form-select"
                        name="estrelas"
                        value={form.estrelas}
                        onChange={handleChange}
                      >
                        <option value={3}>3</option>
                        <option value={4}>4</option>
                        <option value={5}>5</option>
                      </select>
                    </div>
                  </div>

                  <div className="col-6">
                    <div className="mb-3">
                      <label className="form-label">Status</label>
                      <select
                        className="form-select"
                        name="status"
                        value={form.status}
                        onChange={handleChange}
                      >
                        <option value="Ativo">Ativo</option>
                        <option value="Destaque">Destaque</option>
                        <option value="Em revisão">Em revisão</option>
                        <option value="Inativo">Inativo</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="mb-3">
                  <label className="form-label">Diária</label>
                  <input
                    type="text"
                    className="form-control"
                    name="diaria"
                    value={form.diaria}
                    onChange={handleChange}
                    placeholder="R$ 450"
                  />
                </div>

                <div className="d-flex gap-2">
                  <button type="submit" className="btn btn-primary flex-fill" disabled={carregando}>
                    {editandoId !== null ? 'Salvar alterações' : 'Cadastrar hotel'}
                  </button>

                  {editandoId !== null && (
                    <button type="button" className="btn btn-outline-secondary" onClick={handleCancelar}>
                      Cancelar
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
        </div>

        <div className="col-lg-8">
          <div className="card shadow-sm admin-card">
            <div className="card-body p-4">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h4 className="mb-0">Lista de hotéis</h4>
                <span className="badge bg-primary-subtle text-primary rounded-pill px-3 py-2">
                  {hoteis.length} registros
                </span>
              </div>

              {carregando ? (
                <div className="alert alert-info mb-0">Carregando hotéis...</div>
              ) : (
                <div className="table-responsive">
                  <table className="table align-middle table-hover mb-0 city-table">
                    <thead>
                      <tr>
                        <th>Hotel</th>
                        <th>Cidade</th>
                        <th>Estrelas</th>
                        <th>Diária</th>
                        <th>Status</th>
                        <th className="text-end">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {hoteis.map((hotel) => (
                        <tr key={hotel.id}>
                          <td>
                            <div className="fw-semibold">{hotel.nome}</div>
                          </td>
                          <td>{hotel.cidade_nome || hotel.cidade || '—'}</td>
                          <td>{'⭐'.repeat(hotel.estrelas)}</td>
                          <td>{hotel.diaria}</td>
                          <td>
                            <span className="city-status">{hotel.status}</span>
                          </td>
                          <td className="text-end">
                            <div className="city-actions justify-content-end">
                              <button type="button" className="btn btn-sm btn-outline-primary" onClick={() => handleEditar(hotel)}>
                                Editar
                              </button>
                              <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => handleExcluir(hotel.id)}>
                                Excluir
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
