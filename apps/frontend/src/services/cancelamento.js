import { apiFetch } from './api'

// Simula o cancelamento: devolve data limite, multa e reembolso (nao altera nada).
export function consultarMulta(reservaId) {
  return apiFetch(`/reservas/${reservaId}/multa`)
}

// Efetiva o cancelamento. A resposta traz status, multa e data_cancelamento.
export function cancelarReserva(reservaId) {
  return apiFetch(`/reservas/${reservaId}/cancelar`, { method: 'POST' })
}
