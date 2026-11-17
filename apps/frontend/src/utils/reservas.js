export const STATUS_RESERVA = {
  Pendente: { rotulo: 'Pendente', classe: 'text-bg-warning' },
  Confirmada: { rotulo: 'Confirmada', classe: 'text-bg-success' },
  Cancelada: { rotulo: 'Cancelada', classe: 'text-bg-danger' },
}

export const LISTA_STATUS = Object.keys(STATUS_RESERVA)

export function infoStatus(status) {
  return (
    STATUS_RESERVA[status] ?? {
      rotulo: status || 'Desconhecido',
      classe: 'text-bg-secondary',
    }
  )
}

export function formatarDataIso(dataIso) {
  if (!dataIso) return '-'
  const [ano, mes, dia] = String(dataIso).slice(0, 10).split('-')
  return `${dia}/${mes}/${ano}`
}

export function formatarDataHora(dataHoraIso) {
  const data = new Date(dataHoraIso)
  if (Number.isNaN(data.getTime())) return '-'
  return data.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

export function formatarValor(valor) {
  const numero = Number(valor)
  if (!Number.isFinite(numero)) return '-'
  return numero.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function contarNoites(dataEntrada, dataSaida) {
  const [ae, me, de] = String(dataEntrada).slice(0, 10).split('-').map(Number)
  const [as, ms, ds] = String(dataSaida).slice(0, 10).split('-').map(Number)
  const dias = (Date.UTC(as, ms - 1, ds) - Date.UTC(ae, me - 1, de)) / 86400000
  return Number.isFinite(dias) && dias > 0 ? dias : 0
}

export function descreverHospedes(adultos, criancas) {
  const partes = [`${adultos} ${adultos === 1 ? 'adulto' : 'adultos'}`]
  if (criancas > 0) {
    partes.push(`${criancas} ${criancas === 1 ? 'criança' : 'crianças'}`)
  }
  return partes.join(', ')
}

export function ordenarMaisRecentes(reservas) {
  return [...reservas].sort((a, b) => new Date(b.criado_em) - new Date(a.criado_em))
}

export function filtrarPorStatus(reservas, status) {
  if (!status) return reservas
  return reservas.filter((reserva) => reserva.status === status)
}

export function contarPorStatus(reservas) {
  const contagem = Object.fromEntries(LISTA_STATUS.map((status) => [status, 0]))
  for (const reserva of reservas) {
    if (reserva.status in contagem) contagem[reserva.status] += 1
  }
  return contagem
}

export function codigoCurto(id) {
  return String(id).slice(0, 8).toUpperCase()
}