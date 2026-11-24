import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  dataLimiteCancelamento,
  montarAviso,
  normalizarMulta,
  podeCancelar,
  resumirCancelamento,
  tipoDeMulta,
} from '../src/utils/cancelamento.js'

const AGORA = new Date(2026, 10, 24, 15, 0, 0) // 24/11/2026 15:00 (horario local)

const resposta = (extra = {}) => ({
  reserva_id: 'r1',
  nao_reembolsavel: false,
  dentro_do_prazo: true,
  prazo_limite: '2026-12-08T14:00:00-03:00',
  valor_total: '600.00',
  valor_multa: '0.00',
  percentual_multa: '0',
  valor_reembolso: '600.00',
  motivo: 'Cancelamento dentro do prazo',
  ...extra,
})

const nbsp = (texto) => texto.replace(/\s/g, ' ')

test('so Pendente e Confirmada com check-in futuro podem ser canceladas', () => {
  const base = { data_entrada: '2026-12-01' }
  assert.equal(podeCancelar({ ...base, status: 'Pendente' }, AGORA), true)
  assert.equal(podeCancelar({ ...base, status: 'Confirmada' }, AGORA), true)
  assert.equal(podeCancelar({ ...base, status: 'Cancelada' }, AGORA), false)
  assert.equal(podeCancelar({ ...base, status: 'Processando' }, AGORA), false)
  assert.equal(podeCancelar(null, AGORA), false)
})

test('reserva que comeca hoje ou ja comecou nao mostra o botao', () => {
  assert.equal(podeCancelar({ status: 'Confirmada', data_entrada: '2026-11-24' }, AGORA), false)
  assert.equal(podeCancelar({ status: 'Confirmada', data_entrada: '2026-11-20' }, AGORA), false)
  assert.equal(podeCancelar({ status: 'Confirmada', data_entrada: '2026-11-25' }, AGORA), true)
})

test('data limite aceita data_limite_cancelamento ou prazo_limite', () => {
  assert.equal(dataLimiteCancelamento({ data_limite_cancelamento: 'A', prazo_limite: 'B' }), 'A')
  assert.equal(dataLimiteCancelamento({ prazo_limite: 'B' }), 'B')
  assert.equal(dataLimiteCancelamento({}), null)
  assert.equal(dataLimiteCancelamento(undefined), null)
})

test('normalizarMulta converte o contrato do backend', () => {
  const multa = normalizarMulta(resposta({ dentro_do_prazo: false, valor_multa: '200.00' }))
  assert.equal(multa.dentroDoPrazo, false)
  assert.equal(multa.valorMulta, '200.00')
  assert.equal(multa.dataLimite, '2026-12-08T14:00:00-03:00')
})

test('quatro cenarios: tipo de multa', () => {
  assert.equal(tipoDeMulta(normalizarMulta(resposta())), 'sem_multa')
  assert.equal(tipoDeMulta(normalizarMulta(resposta({ dentro_do_prazo: false }))), 'multa_diaria')
  assert.equal(tipoDeMulta(normalizarMulta(resposta({ nao_reembolsavel: true }))), 'nao_reembolsavel')
  // nao reembolsavel dentro ou fora do prazo: sempre 100%
  assert.equal(
    tipoDeMulta(normalizarMulta(resposta({ nao_reembolsavel: true, dentro_do_prazo: false }))),
    'nao_reembolsavel',
  )
})

test('aviso: reembolsavel dentro do prazo e sem multa', () => {
  const aviso = montarAviso(normalizarMulta(resposta()))
  assert.equal(aviso.tipo, 'success')
  assert.match(nbsp(aviso.texto), /sem custo até 08\/12\/2026/)
  assert.match(nbsp(aviso.texto), /R\$ 600,00/)
})

test('aviso: reembolsavel fora do prazo cobra uma diaria', () => {
  const aviso = montarAviso(
    normalizarMulta(
      resposta({ dentro_do_prazo: false, valor_multa: '200.00', valor_reembolso: '400.00', percentual_multa: '33.33' }),
    ),
  )
  assert.equal(aviso.tipo, 'warning')
  assert.match(nbsp(aviso.texto), /multa de uma diária \(R\$ 200,00\)/)
  assert.match(nbsp(aviso.texto), /reembolsar: R\$ 400,00/)
})

test('aviso: nao reembolsavel perde 100%', () => {
  const aviso = montarAviso(
    normalizarMulta(
      resposta({ nao_reembolsavel: true, valor_multa: '600.00', valor_reembolso: '0.00', percentual_multa: '100' }),
    ),
  )
  assert.equal(aviso.tipo, 'danger')
  assert.match(aviso.texto, /100%/)
  assert.match(nbsp(aviso.texto), /R\$ 600,00/)
})

test('aviso sem data limite nao mostra "undefined" nem "-"', () => {
  const aviso = montarAviso(normalizarMulta(resposta({ prazo_limite: undefined })))
  assert.doesNotMatch(aviso.texto, /undefined|null/)
})

test('resumo do cancelamento com e sem multa', () => {
  assert.equal(resumirCancelamento('AB12', '0.00'), 'Reserva #AB12 cancelada sem multa.')
  assert.equal(resumirCancelamento('AB12', null), 'Reserva #AB12 cancelada sem multa.')
  assert.match(nbsp(resumirCancelamento('AB12', '200.00')), /Multa aplicada: R\$ 200,00/)
})
