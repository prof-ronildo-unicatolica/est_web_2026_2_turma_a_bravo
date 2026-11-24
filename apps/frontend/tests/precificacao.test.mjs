// Testes do motor de precificacao do frontend (src/utils/precificacao.js).
// Rodar: npm test   (usa o test runner nativo do Node, sem dependencias extras)
//
// Os casos de preco vem de apps/shared/precificacao_casos.json, o MESMO arquivo lido pelo
// teste do backend (tests/test_precificacao_paridade.py). Se o front e o back divergirem,
// um dos dois testes falha.

import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

import {
  calcularCotacao,
  calcularServico,
  calcularTotalServicos,
  dividirArredondando,
  paraBasisPoints,
  paraCentavos,
  pessoasParaServicos,
} from '../src/utils/precificacao.js'

const arquivo = fileURLToPath(new URL('../../shared/precificacao_casos.json', import.meta.url))
const { padrao_entrada: padraoEntrada, padrao_esperado: padraoEsperado, casos } = JSON.parse(
  readFileSync(arquivo, 'utf8'),
)

// Converte o formato do arquivo compartilhado para o que o Checkout.jsx entrega ao motor
// (mesmas conversoes: paraCentavos e paraBasisPoints). Cada caso so informa o que difere
// de padrao_entrada.
function paraEntradaFrontend(entradaDoCaso) {
  const e = { ...padraoEntrada, ...entradaDoCaso }
  return {
    precoDiariaCentavos: paraCentavos(e.preco_diaria),
    checkIn: e.check_in,
    checkOut: e.check_out,
    adultos: e.adultos,
    idadesCriancas: e.idades_criancas,
    naoReembolsavel: e.nao_reembolsavel,
    horarioCheckin: e.horario_checkin,
    horarioCheckout: e.horario_checkout,
    tarifasTemporada: e.tarifas.map((t) => ({
      nome: t.nome,
      dataInicio: t.data_inicio,
      dataFim: t.data_fim,
      ajusteBp: paraBasisPoints(t.percentual_ajuste),
    })),
    maxAdultos: e.max_adultos,
    maxCriancas: e.max_criancas,
  }
}

test('o arquivo compartilhado tem casos suficientes', () => {
  assert.ok(casos.length >= 40, `esperava ao menos 40 casos, achei ${casos.length}`)
  assert.ok(casos.some((c) => c.erro), 'faltam casos de entrada invalida')
})

for (const caso of casos) {
  test(`paridade com o backend: ${caso.nome}`, () => {
    const { erros, cotacao } = calcularCotacao(paraEntradaFrontend(caso.entrada))

    if (caso.erro) {
      assert.ok(erros.length > 0, 'o frontend deveria recusar esta entrada')
      assert.equal(cotacao, null)
      return
    }

    assert.deepEqual(erros, [])
    const esperado = { ...padraoEsperado, ...caso.esperado }
    assert.equal(cotacao.noites, esperado.noites)
    assert.deepEqual(
      cotacao.detalheNoites.map((noite) => noite.valor),
      esperado.detalhe_noites_centavos,
    )
    assert.equal(cotacao.subtotalDiarias, esperado.subtotal_centavos)
    assert.equal(cotacao.taxaEarlyCheckin, esperado.early_centavos)
    assert.equal(cotacao.taxaLateCheckout, esperado.late_centavos)
    assert.equal(cotacao.descontoNaoReembolsavel, esperado.desconto_centavos)
    assert.equal(cotacao.total, esperado.total_centavos)
    assert.equal(cotacao.bebes, esperado.bebes)
    assert.equal(cotacao.criancasPagantes, esperado.criancas_pagantes)
  })
}

// --- Helpers de arredondamento -------------------------------------------------------
test('dividirArredondando arredonda meio para cima', () => {
  assert.equal(dividirArredondando(5, 2), 3)
  assert.equal(dividirArredondando(4, 2), 2)
  assert.equal(dividirArredondando(3, 2), 2)
  assert.equal(dividirArredondando(1505, 10), 151)
})

test('paraCentavos e paraBasisPoints convertem sem erro de ponto flutuante', () => {
  assert.equal(paraCentavos('10.03'), 1003)
  assert.equal(paraCentavos('99.99'), 9999)
  assert.equal(paraBasisPoints('12.35'), 1235)
  assert.equal(paraBasisPoints('-10.00'), -1000)
})

// --- Servicos adicionais: so existem no frontend (o backend ainda nao calcula) -------
// Valores fixos calculados a mao.
test('servico por_pessoa_dia: preco x pessoas x noites', () => {
  const servico = { preco: '25.00', tipo_cobranca: 'por_pessoa_dia' }
  assert.equal(calcularServico(servico, { pessoas: 3, noites: 2 }), 15000)
})

test('servico por_diaria: preco x noites, independe de pessoas', () => {
  const servico = { preco: '80.00', tipo_cobranca: 'por_diaria' }
  assert.equal(calcularServico(servico, { pessoas: 5, noites: 3 }), 24000)
})

test('servico por_servico: preco x quantidade (padrao 1)', () => {
  const servico = { preco: '50.00', tipo_cobranca: 'por_servico' }
  assert.equal(calcularServico(servico, { pessoas: 2, noites: 4, quantidade: 2 }), 10000)
  assert.equal(calcularServico(servico, { pessoas: 2, noites: 4 }), 5000)
})

test('bebes nao contam como pessoa nos servicos', () => {
  // 2 adultos + bebe (1) + crianca (5) + adolescente (15) = 4 pessoas
  assert.equal(pessoasParaServicos(2, [1, 5, 15]), 4)
})

test('total dos servicos soma todos os selecionados', () => {
  const selecionados = [
    { servico: { preco: '25.00', tipo_cobranca: 'por_pessoa_dia' }, quantidade: 1 },
    { servico: { preco: '80.00', tipo_cobranca: 'por_diaria' }, quantidade: 1 },
    { servico: { preco: '50.00', tipo_cobranca: 'por_servico' }, quantidade: 2 },
  ]
  // 25 x 2 pessoas x 3 noites + 80 x 3 noites + 50 x 2 = 150 + 240 + 100
  assert.equal(calcularTotalServicos(selecionados, { pessoas: 2, noites: 3 }), 49000)
})