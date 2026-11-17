import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'
import StatusBadge from '../components/StatusBadge'
import {
  LISTA_STATUS,
  codigoCurto,
  contarNoites,
  contarPorStatus,
  descreverHospedes,
  filtrarPorStatus,
  formatarDataHora,
  formatarDataIso,
  formatarValor,
  ordenarMaisRecentes,
} from '../utils/reservas'

const ENDPOINT_RESERVAS = '/reservas/minhas'

export default function MinhasReservas() {
  const navigate = useNavigate()

  const [reservas, setReservas] = useState([])
  const [quartos, setQuartos] = useState([])
  const [hoteis, setHoteis] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [filtro, setFiltro] = useState('')

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro('')

    try {
      const [listaReservas, listaQuartos, listaHoteis] = await Promise.all([
        apiFetch(ENDPOINT_RESERVAS),
        apiFetch('/quartos').catch(() => []),
        apiFetch('/hoteis').catch(() => []),
      ])

      setReservas(ordenarMaisRecentes(listaReservas))
      setQuartos(listaQuartos)
      setHoteis(listaHoteis)
    } catch (erroApi) {
      if (erroApi.message === '401') {
        navigate('/login')
        return
      }

      setErro('Não foi possível carregar suas reservas. Tente novamente.')
    } finally {
      setCarregando(false)
    }
  }, [navigate])

  useEffect(() => {
    carregar()
  }, [carregar])

  const quartoPorId = useMemo(
    () => Object.fromEntries(quartos.map((quarto) => [quarto.id, quarto])),
    [quartos],
  )

  const hotelPorId = useMemo(
    () => Object.fromEntries(hoteis.map((hotel) => [hotel.id, hotel])),
    [hoteis],
  )

  const contagem = useMemo(() => contarPorStatus(reservas), [reservas])
  const visiveis = useMemo(() => filtrarPorStatus(reservas, filtro), [reservas, filtro])

  function descreverQuarto(reserva) {
    const quarto = quartoPorId[reserva.quarto_id]
    if (!quarto) return { hotel: 'Quarto', tipo: codigoCurto(reserva.quarto_id) }

    const hotel = hotelPorId[quarto.hotel_id]
    return { hotel: hotel ? hotel.nome : 'Hotel', tipo: quarto.tipo }
  }

  return (
    <div className="card shadow-sm">
      <div className="card-body p-4">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
          <div>
            <h2 className="mb-1">Minhas reservas</h2>
            <p className="text-muted mb-0">
              Acompanhe o andamento das reservas que você solicitou.
            </p>
          </div>

          <button
            type="button"
            className="btn btn-outline-secondary btn-sm"
            onClick={carregar}
            disabled={carregando}
          >
            {carregando ? 'Atualizando...' : 'Atualizar'}
          </button>
        </div>

        {erro && (
          <div className="alert alert-danger d-flex justify-content-between align-items-center">
            <span>{erro}</span>
            <button type="button" className="btn btn-sm btn-outline-danger" onClick={carregar}>
              Tentar novamente
            </button>
          </div>
        )}

        {carregando && reservas.length === 0 && !erro && (
          <div className="alert alert-info mb-0">Carregando reservas...</div>
        )}

        {!carregando && !erro && reservas.length === 0 && (
          <div className="text-center py-5">
            <p className="fs-5 mb-1">Você ainda não tem reservas.</p>
            <p className="text-muted">Escolha um hotel e faça sua primeira reserva.</p>
            <Link to="/checkout" className="btn btn-primary">
              Fazer uma reserva
            </Link>
          </div>
        )}

        {reservas.length > 0 && (
          <>
            <div className="btn-group btn-group-sm mb-3 flex-wrap" role="group" aria-label="Filtrar por status">
              <button
                type="button"
                className={`btn ${filtro === '' ? 'btn-dark' : 'btn-outline-dark'}`}
                onClick={() => setFiltro('')}
              >
                Todas ({reservas.length})
              </button>

              {LISTA_STATUS.map((status) => (
                <button
                  key={status}
                  type="button"
                  className={`btn ${filtro === status ? 'btn-dark' : 'btn-outline-dark'}`}
                  onClick={() => setFiltro(status)}
                >
                  {status} ({contagem[status]})
                </button>
              ))}
            </div>

            {visiveis.length === 0 ? (
              <div className="alert alert-light border mb-0">
                Nenhuma reserva com o status selecionado.
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover align-middle mb-0">
                  <thead className="table-light">
                    <tr>
                      <th>Reserva</th>
                      <th>Hotel / Quarto</th>
                      <th>Período</th>
                      <th>Hóspedes</th>
                      <th className="text-end">Valor</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {visiveis.map((reserva) => {
                      const { hotel, tipo } = descreverQuarto(reserva)
                      const noites = contarNoites(reserva.data_entrada, reserva.data_saida)

                      return (
                        <tr key={reserva.id}>
                          <td>
                            <div className="fw-semibold">#{codigoCurto(reserva.id)}</div>
                            <small className="text-muted">{formatarDataHora(reserva.criado_em)}</small>
                          </td>
                          <td>
                            <div>{hotel}</div>
                            <small className="text-muted">{tipo}</small>
                          </td>
                          <td>
                            <div>
                              {formatarDataIso(reserva.data_entrada)} a {formatarDataIso(reserva.data_saida)}
                            </div>
                            <small className="text-muted">
                              {noites} {noites === 1 ? 'noite' : 'noites'}
                            </small>
                          </td>
                          <td>{descreverHospedes(reserva.quantidade_adultos, reserva.quantidade_criancas)}</td>
                          <td className="text-end fw-semibold">{formatarValor(reserva.valor_total)}</td>
                          <td>
                            <StatusBadge status={reserva.status} />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}