import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  codigoCurto,
  contarNoites,
  contarPorStatus,
  descreverHospedes,
  filtrarPorStatus,
  formatarDataIso,
  formatarValor,
  infoStatus,
  ordenarMaisRecentes,
} from '../src/utils/reservas.js'

const reservas = [
  { id: 'a1', status: 'Pendente', criado_em: '2026-11-10T10:00:00Z' },
  { id: 'b2', status: 'Confirmada', criado_em: '2026-11-12T10:00:00Z' },
  { id: 'c3', status: 'Cancelada', criado_em: '2026-11-11T10:00:00Z' },
  { id: 'd4', status: 'Confirmada', criado_em: '2026-11-09T10:00:00Z' },
]

test('cada status tem sua cor de badge', () => {
  assert.equal(infoStatus('Pendente').classe, 'text-bg-warning')
  assert.equal(infoStatus('Confirmada').classe, 'text-bg-success')
  assert.equal(infoStatus('Cancelada').classe, 'text-bg-danger')
})

test('status desconhecido cai em badge neutro e mantem o texto', () => {
  assert.deepEqual(infoStatus('Em analise'), { rotulo: 'Em analise', classe: 'text-bg-secondary' })
  assert.equal(infoStatus(undefined).rotulo, 'Desconhecido')
})

test('formatarDataIso nao desloca o dia', () => {
  assert.equal(formatarDataIso('2026-12-05'), '05/12/2026')
  assert.equal(formatarDataIso(null), '-')
})

test('formatarValor aceita texto do Decimal e formata em reais', () => {
  assert.equal(formatarValor('450.00').replace(/\s/g, ' '), 'R$ 450,00')
  assert.equal(formatarValor('1234.5').replace(/\s/g, ' '), 'R$ 1.234,50')
  assert.equal(formatarValor('abc'), '-')
})

test('contarNoites ignora o dia da saida e atravessa virada de mes', () => {
  assert.equal(contarNoites('2026-12-05', '2026-12-08'), 3)
  assert.equal(contarNoites('2026-12-30', '2027-01-02'), 3)
  assert.equal(contarNoites('2026-12-05', '2026-12-05'), 0)
})

test('descreverHospedes usa singular e plural', () => {
  assert.equal(descreverHospedes(1, 0), '1 adulto')
  assert.equal(descreverHospedes(2, 1), '2 adultos, 1 criança')
  assert.equal(descreverHospedes(2, 3), '2 adultos, 3 crianças')
})

test('ordenarMaisRecentes coloca a ultima solicitacao primeiro sem alterar a lista original', () => {
  const ordenadas = ordenarMaisRecentes(reservas)
  assert.deepEqual(ordenadas.map((r) => r.id), ['b2', 'c3', 'a1', 'd4'])
  assert.equal(reservas[0].id, 'a1')
})

test('filtrarPorStatus e contarPorStatus', () => {
  assert.equal(filtrarPorStatus(reservas, '').length, 4)
  assert.deepEqual(filtrarPorStatus(reservas, 'Confirmada').map((r) => r.id), ['b2', 'd4'])
  assert.deepEqual(contarPorStatus(reservas), { Pendente: 1, Confirmada: 2, Cancelada: 1 })
})

test('codigoCurto', () => {
  assert.equal(codigoCurto('3f2a9c1e-1111-2222-3333-444455556666'), '3F2A9C1E')
})