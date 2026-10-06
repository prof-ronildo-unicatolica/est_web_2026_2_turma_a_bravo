import { useEffect, useState } from 'react'
import { apiFetch } from '../services/api'

const estadoInicial = {
  nome: '',
  uf: '',
  status: 'Ativa'
}

export default function Cidades() {
  const [cidades, setCidades] = useState([])
  const [form, setForm] = useState(estadoInicial)
  const [editandoId, setEditandoId] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')

  async function carregarCidades() {
    try {
      setErro('')
      const dados = await apiFetch('/cidades')
      setCidades(dados)
    } catch {
      setErro('Não foi possível carregar as cidades.')
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarCidades()
  }, [])

  function handleChange(event) {
    const { name, value } = event.target
    setForm((atual) => ({ ...atual, [name]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()

    if (!form.nome.trim() || !form.uf.trim()) {
      alert('Informe o nome e a UF da cidade.')
      return
    }

    try {
      const payload = {
        nome: form.nome.trim(),
        uf: form.uf.trim().toUpperCase(),
        status: form.status
      }

      if (editandoId !== null) {
        await apiFetch(`/cidades/${editandoId}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        })
      } else {
        await apiFetch('/cidades', {
          method: 'POST',
          body: JSON.stringify(payload)
        })
      }

      await carregarCidades()
      setEditandoId(null)
      setForm(estadoInicial)
    } catch {
      alert('Não foi possível salvar a cidade.')
    }
  }

  function handleEditar(cidade) {
    setEditandoId(cidade.id)
    setForm({
      nome: cidade.nome,
      uf: cidade.uf,
      status: cidade.status
    })
  }

  async function handleExcluir(id) {
    try {
      await apiFetch(`/cidades/${id}`, { method: 'DELETE' })
      await carregarCidades()

      if (editandoId === id) {
        setEditandoId(null)
        setForm(estadoInicial)
      }
    } catch {
      alert('Não foi possível excluir a cidade.')
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
          <span className="admin-badge">Gestão de cidades</span>
          <h2 className="mb-1 mt-3">Cidades atendidas</h2>
          <p className="mb-0 text-secondary">
            Cadastre, edite e acompanhe as unidades da rede hoteleira.
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
              <h4 className="mb-3">{editandoId !== null ? 'Editar cidade' : 'Nova cidade'}</h4>

              <form onSubmit={handleSubmit} className="city-form">
                <div className="mb-3">
                  <label className="form-label">Nome da cidade</label>
                  <input
                    type="text"
                    className="form-control"
                    name="nome"
                    value={form.nome}
                    onChange={handleChange}
                    placeholder="Ex.: Curitiba"
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">UF</label>
                  <input
                    type="text"
                    className="form-control"
                    name="uf"
                    maxLength={2}
                    value={form.uf}
                    onChange={handleChange}
                    placeholder="SP"
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Status</label>
                  <select
                    className="form-select"
                    name="status"
                    value={form.status}
                    onChange={handleChange}
                  >
                    <option value="Ativa">Ativa</option>
                    <option value="Destaque">Destaque</option>
                    <option value="Em expansão">Em expansão</option>
                    <option value="Inativa">Inativa</option>
                  </select>
                </div>

                <div className="d-flex gap-2">
                  <button type="submit" className="btn btn-primary flex-fill" disabled={carregando}>
                    {editandoId !== null ? 'Salvar alterações' : 'Cadastrar cidade'}
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
                <h4 className="mb-0">Lista de cidades</h4>
                <span className="badge bg-primary-subtle text-primary rounded-pill px-3 py-2">
                  {cidades.length} registros
                </span>
              </div>

              {carregando ? (
                <div className="alert alert-info mb-0">Carregando cidades...</div>
              ) : (
                <div className="table-responsive">
                  <table className="table align-middle table-hover mb-0 city-table">
                    <thead>
                      <tr>
                        <th>Cidade</th>
                        <th>UF</th>
                        <th>Hotéis</th>
                        <th>Status</th>
                        <th className="text-end">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cidades.map((cidade) => (
                        <tr key={cidade.id}>
                          <td>
                            <div className="fw-semibold">{cidade.nome}</div>
                          </td>
                          <td>
                            <span className="city-uf">{cidade.uf}</span>
                          </td>
                          <td>{cidade.hoteis}</td>
                          <td>
                            <span className="city-status">{cidade.status}</span>
                          </td>
                          <td className="text-end">
                            <div className="city-actions justify-content-end">
                              <button type="button" className="btn btn-sm btn-outline-primary" onClick={() => handleEditar(cidade)}>
                                Editar
                              </button>
                              <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => handleExcluir(cidade.id)}>
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
