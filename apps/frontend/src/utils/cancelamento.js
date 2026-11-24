import { formatarDataHora, formatarValor } from './reservas.js'

// Reservas nesses status ainda podem ser canceladas pelo cliente.
export const STATUS_CANCELAVEIS = ['Pendente', 'Confirmada']

function dataLocalIso(agora) {
  const mes = String(agora.getMonth() + 1).padStart(2, '0')
  const dia = String(agora.getDate()).padStart(2, '0')
  return `${agora.getFullYear()}-${mes}-${dia}`
}

// Mostra o botao so quando o backend aceitaria o cancelamento:
// status cancelavel e check-in ainda no futuro (reserva iniciada nao cancela).
export function podeCancelar(reserva, agora = new Date()) {
  if (!reserva || !STATUS_CANCELAVEIS.includes(reserva.status)) return false
  return String(reserva.data_entrada).slice(0, 10) > dataLocalIso(agora)
}

// Aceita o nome do contrato da sprint (data_limite_cancelamento) e o nome que
// o endpoint de multas devolve hoje (prazo_limite).
export function dataLimiteCancelamento(dados) {
  return dados?.data_limite_cancelamento ?? dados?.prazo_limite ?? null
}

// Converte a resposta do backend em um objeto unico. Os valores em dinheiro
// continuam como vieram (texto do Decimal): quem calcula a multa e o backend,
// o frontend so exibe, assim os dois nunca divergem.
export function normalizarMulta(dados) {
  return {
    reservaId: dados.reserva_id,
    dataLimite: dataLimiteCancelamento(dados),
    dentroDoPrazo: Boolean(dados.dentro_do_prazo),
    naoReembolsavel: Boolean(dados.nao_reembolsavel),
    valorTotal: dados.valor_total,
    valorMulta: dados.valor_multa,
    percentualMulta: dados.percentual_multa,
    valorReembolso: dados.valor_reembolso,
    motivo: dados.motivo ?? '',
  }
}

export function tipoDeMulta(multa) {
  if (multa.naoReembolsavel) return 'nao_reembolsavel'
  return multa.dentroDoPrazo ? 'sem_multa' : 'multa_diaria'
}

// Texto do aviso exibido antes de confirmar. `tipo` vira a cor do alerta.
export function montarAviso(multa) {
  const limite = multa.dataLimite ? formatarDataHora(multa.dataLimite) : null
  const valorMulta = formatarValor(multa.valorMulta)
  const reembolso = formatarValor(multa.valorReembolso)

  switch (tipoDeMulta(multa)) {
    case 'nao_reembolsavel':
      return {
        tipo: 'danger',
        titulo: 'Tarifa não reembolsável',
        texto:
          `Esta tarifa não tem cancelamento gratuito: a multa é de 100% do valor da reserva (${valorMulta}). ` +
          `Valor a reembolsar: ${reembolso}.`,
      }
    case 'multa_diaria':
      return {
        tipo: 'warning',
        titulo: 'Cancelamento fora do prazo gratuito',
        texto:
          `${limite ? `O prazo para cancelar sem multa terminou em ${limite}. ` : ''}` +
          `Será cobrada uma multa de uma diária (${valorMulta}). Valor a reembolsar: ${reembolso}.`,
      }
    default:
      return {
        tipo: 'success',
        titulo: 'Cancelamento sem multa',
        texto:
          `${limite ? `Você pode cancelar sem custo até ${limite}. ` : 'Você pode cancelar sem custo. '}` +
          `Valor a reembolsar: ${reembolso}.`,
      }
  }
}

export function resumirCancelamento(codigo, multa) {
  const valor = Number(multa)
  if (!Number.isFinite(valor) || valor <= 0) {
    return `Reserva #${codigo} cancelada sem multa.`
  }
  return `Reserva #${codigo} cancelada. Multa aplicada: ${formatarValor(multa)}.`
}
