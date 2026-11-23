import { useEffect, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { apiFetch } from '../services/api'
import { formatarMoeda, paraCentavos } from '../utils/precificacao'

const INTERVALO_MS = 3000

function formatarData(dataIso) {
  return dataIso.split('-').reverse().join('/')
}

export default function ReservaStatus() {
  const { id } = useParams()
  const [reserva, setReserva] = useState(null)
  const [erro, setErro] = useState('')
  const [detalhes, setDetalhes] = useState(null)

  // Consulta o status da reserva a cada 3 segundos enquanto ela estiver em andamento.
  useEffect(() => {
    let ativo = true
    let temporizador = null

    async function consultar() {
      try {
        const dados = await apiFetch(`/reservas/${id}`)
        if (!ativo) return
        setReserva(dados)
        setErro('')
        if (dados.status === 'Pendente' || dados.status === 'Processando') {
          temporizador = setTimeout(consultar, INTERVALO_MS)
        }
      } catch (e) {
        if (!ativo) return
        setErro(e.message)
        // Falha de rede ou do servidor: tenta de novo. 401 e 404 nao adianta repetir.
        if (e.message !== '401' && e.status !== 404) {
          temporizador = setTimeout(consultar, INTERVALO_MS)
        }
      }
    }

    consultar()

    return () => {
      ativo = false
      clearTimeout(temporizador)
    }
  }, [id])

  // Quando a reserva e confirmada, busca nome do hotel e tipo do quarto para o voucher.
  const status = reserva ? reserva.status : ''
  const quartoId = reserva ? reserva.quarto_id : ''

  useEffect(() => {
    if (status !== 'Confirmada') return undefined
    let ativo = true

    Promise.all([apiFetch('/quartos'), apiFetch('/hoteis')])
      .then(([quartos, hoteis]) => {
        const quarto = quartos.find((item) => item.id === quartoId)
        const hotel = quarto ? hoteis.find((item) => item.id === quarto.hotel_id) : null
        if (ativo) setDetalhes({ quarto, hotel })
      })
      .catch(() => {
        // O voucher funciona sem esses detalhes.
      })

    return () => {
      ativo = false
    }
  }, [status, quartoId])

  if (erro === '401') {
    return <Navigate to="/login" replace />
  }

  if (!reserva) {
    if (erro) {
      return (
        <div className="alert alert-danger">
          Não foi possível consultar a reserva: {erro}
          <div className="mt-3">
            <Link className="btn btn-outline-primary btn-sm" to="/checkout">
              Voltar ao checkout
            </Link>
          </div>
        </div>
      )
    }
    return <div className="alert alert-info">Carregando reserva...</div>
  }

  const codigo = reserva.id.slice(0, 8).toUpperCase()

  // --- Processando ---
  if (reserva.status === 'Pendente' || reserva.status === 'Processando') {
    return (
      <div className="card shadow-sm text-center">
        <div className="card-body py-5">
          <div className="spinner-border text-primary mb-3" role="status">
            <span className="visually-hidden">Processando...</span>
          </div>
          <h2 className="h4">Processando sua reserva</h2>
          <p className="text-secondary mb-1">
            Estamos verificando a disponibilidade e confirmando o pagamento.
          </p>
          <p className="text-secondary small mb-0">
            Código {codigo} · atualizando a cada 3 segundos
          </p>
          {erro && (
            <div className="alert alert-warning small mt-3 mb-0">
              Falha ao atualizar ({erro}). Tentando novamente...
            </div>
          )}
        </div>
      </div>
    )
  }

  // --- Voucher ---
  if (reserva.status === 'Confirmada') {
    const hotel = detalhes ? detalhes.hotel : null
    const quarto = detalhes ? detalhes.quarto : null
    const hospedes = reserva.quantidade_adultos + reserva.quantidade_criancas

    return (
      <div className="card shadow-sm border-success">
        <div className="card-header bg-success text-white">
          <h2 className="h4 mb-0">Reserva confirmada</h2>
        </div>
        <div className="card-body">
          <p className="text-secondary mb-3">Voucher nº {codigo}</p>

          <dl className="row mb-0">
            <dt className="col-sm-4">Hotel</dt>
            <dd className="col-sm-8">{hotel ? hotel.nome : '—'}</dd>

            <dt className="col-sm-4">Quarto</dt>
            <dd className="col-sm-8">{quarto ? quarto.tipo : '—'}</dd>

            <dt className="col-sm-4">Entrada</dt>
            <dd className="col-sm-8">{formatarData(reserva.data_entrada)}</dd>

            <dt className="col-sm-4">Saída</dt>
            <dd className="col-sm-8">{formatarData(reserva.data_saida)}</dd>

            <dt className="col-sm-4">Hóspedes</dt>
            <dd className="col-sm-8">
              {reserva.quantidade_adultos} adulto(s)
              {reserva.quantidade_criancas > 0 && `, ${reserva.quantidade_criancas} criança(s)`}
              {' '}({hospedes} no total)
            </dd>

            <dt className="col-sm-4">Valor total</dt>
            <dd className="col-sm-8 fw-bold">
              {formatarMoeda(paraCentavos(reserva.valor_total))}
            </dd>
          </dl>
        </div>
        <div className="card-footer d-flex gap-2">
          <button type="button" className="btn btn-outline-secondary" onClick={() => window.print()}>
            Imprimir voucher
          </button>
          <Link className="btn btn-primary" to="/checkout">
            Nova reserva
          </Link>
        </div>
      </div>
    )
  }

  // --- Erro (Cancelada ou qualquer outro status final) ---
  return (
    <div className="card shadow-sm border-danger">
      <div className="card-header bg-danger text-white">
        <h2 className="h4 mb-0">Não foi possível confirmar a reserva</h2>
      </div>
      <div className="card-body">
        <p className="mb-2">
          Sua reserva {codigo} foi cancelada. Isso acontece quando o período já foi reservado por
          outro cliente ou quando o pagamento é recusado.
        </p>
        <p className="text-secondary small mb-0">Nenhum valor foi cobrado.</p>
      </div>
      <div className="card-footer">
        <Link className="btn btn-primary" to="/checkout">
          Tentar novamente
        </Link>
      </div>
    </div>
  )
}