export const REGRAS = {
  idadeMaxBebe: 2,
  idadeMaxCrianca: 12,
  checkinPadrao: 14 * 60,
  checkoutPadrao: 12 * 60,
  earlyLimiteDiariaCheia: 6 * 60,
  lateLimiteDiariaCheia: 18 * 60,
  descontoNaoReembolsavel: 10,
}

export function dividirArredondando(numerador, denominador) {
  const resto = numerador % denominador
  const quociente = (numerador - resto) / denominador
  return resto * 2 >= denominador ? quociente + 1 : quociente
}

export function paraCentavos(valor) {
  return Math.round(Number(valor) * 100)
}

export function paraBasisPoints(percentual) {
  return Math.round(Number(percentual) * 100)
}

export function formatarMoeda(centavos) {
  return (centavos / 100).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

export function horarioParaMinutos(horario) {
  if (!horario) return null
  const [horas, minutos] = horario.split(':').map(Number)
  return horas * 60 + minutos
}

function somarDias(dataIso, dias) {
  const [ano, mes, dia] = dataIso.split('-').map(Number)
  const data = new Date(Date.UTC(ano, mes - 1, dia + dias))
  return data.toISOString().slice(0, 10)
}

function contarNoites(checkIn, checkOut) {
  const [a1, m1, d1] = checkIn.split('-').map(Number)
  const [a2, m2, d2] = checkOut.split('-').map(Number)
  const inicio = Date.UTC(a1, m1 - 1, d1)
  const fim = Date.UTC(a2, m2 - 1, d2)
  return Math.round((fim - inicio) / 86400000)
}

export function classificarCriancas(idades) {
  let bebes = 0
  let criancas = 0
  let adolescentes = 0
  for (const idade of idades) {
    if (idade <= REGRAS.idadeMaxBebe) bebes += 1
    else if (idade <= REGRAS.idadeMaxCrianca) criancas += 1
    else adolescentes += 1
  }
  return { bebes, criancas, adolescentes }
}

export function validarEntrada(entrada) {
  const erros = []
  const { precoDiariaCentavos, checkIn, checkOut, adultos, idadesCriancas } = entrada

  if (!(precoDiariaCentavos > 0)) erros.push('Selecione um quarto com diária válida.')
  if (!checkIn || !checkOut) {
    erros.push('Informe as datas de check-in e check-out.')
  } else if (checkOut <= checkIn) {
    erros.push('O check-out deve ser posterior ao check-in.')
  }
  if (!(adultos >= 1)) erros.push('Informe ao menos 1 adulto.')
  for (const idade of idadesCriancas) {
    if (!Number.isInteger(idade) || idade < 0) {
      erros.push('Informe a idade de cada criança (0 a 17).')
      break
    }
    if (idade >= 18) {
      erros.push('Criança deve ter menos de 18 anos; informe como adulto.')
      break
    }
  }
  if (entrada.maxAdultos != null && adultos > entrada.maxAdultos) {
    erros.push(`O quarto comporta no máximo ${entrada.maxAdultos} adulto(s).`)
  }
  if (entrada.maxCriancas != null && idadesCriancas.length > entrada.maxCriancas) {
    erros.push(`O quarto comporta no máximo ${entrada.maxCriancas} criança(s).`)
  }
  return erros
}

function multiplicadorDoDia(dia, tarifas) {
  let melhor = null
  for (const tarifa of tarifas) {
    if (tarifa.dataInicio <= dia && dia <= tarifa.dataFim) {
      if (melhor === null || tarifa.ajusteBp > melhor.ajusteBp) melhor = tarifa
    }
  }
  return melhor
}

function taxaEarlyCheckin(chegada, valorNoite) {
  if (chegada === null || chegada >= REGRAS.checkinPadrao) return 0
  if (chegada < REGRAS.earlyLimiteDiariaCheia) return valorNoite
  return dividirArredondando(valorNoite, 2)
}

function taxaLateCheckout(saida, valorNoite) {
  if (saida === null || saida <= REGRAS.checkoutPadrao) return 0
  if (saida > REGRAS.lateLimiteDiariaCheia) return valorNoite
  return dividirArredondando(valorNoite, 2)
}

export function calcularCotacao(entrada) {
  const erros = validarEntrada(entrada)
  if (erros.length > 0) return { erros, cotacao: null }

  const { bebes, criancas, adolescentes } = classificarCriancas(entrada.idadesCriancas)
  const ocupantesEmMeios = 2 * (entrada.adultos + adolescentes) + criancas
  const totalNoites = contarNoites(entrada.checkIn, entrada.checkOut)
  const tarifas = entrada.tarifasTemporada || []

  const noites = []
  for (let i = 0; i < totalNoites; i += 1) {
    const dia = somarDias(entrada.checkIn, i)
    const tarifa = multiplicadorDoDia(dia, tarifas)
    const ajusteBp = tarifa ? tarifa.ajusteBp : 0
    const valor = dividirArredondando(
      entrada.precoDiariaCentavos * (10000 + ajusteBp) * ocupantesEmMeios,
      20000,
    )
    noites.push({ data: dia, ajusteBp, nomeTarifa: tarifa ? tarifa.nome : null, valor })
  }

  const subtotalDiarias = noites.reduce((soma, noite) => soma + noite.valor, 0)
  const taxaEarly = taxaEarlyCheckin(
    horarioParaMinutos(entrada.horarioCheckin),
    noites[0].valor,
  )
  const taxaLate = taxaLateCheckout(
    horarioParaMinutos(entrada.horarioCheckout),
    noites[noites.length - 1].valor,
  )
  const desconto = entrada.naoReembolsavel
    ? dividirArredondando(subtotalDiarias * REGRAS.descontoNaoReembolsavel, 100)
    : 0

  return {
    erros: [],
    cotacao: {
      noites: totalNoites,
      adultos: entrada.adultos,
      criancasPagantes: criancas + adolescentes,
      bebes,
      detalheNoites: noites,
      subtotalDiarias,
      taxaEarlyCheckin: taxaEarly,
      taxaLateCheckout: taxaLate,
      descontoNaoReembolsavel: desconto,
      total: subtotalDiarias + taxaEarly + taxaLate - desconto,
    },
  }
}

export function pessoasParaServicos(adultos, idadesCriancas) {
  const { criancas, adolescentes } = classificarCriancas(idadesCriancas)
  return adultos + criancas + adolescentes
}

export function calcularServico(servico, contexto) {
  const preco = paraCentavos(servico.preco)
  if (servico.tipo_cobranca === 'por_pessoa_dia') {
    return preco * contexto.pessoas * contexto.noites
  }
  if (servico.tipo_cobranca === 'por_diaria') {
    return preco * contexto.noites
  }
  return preco * (contexto.quantidade || 1)
}

export function calcularTotalServicos(servicosSelecionados, contexto) {
  return servicosSelecionados.reduce(
    (soma, item) =>
      soma +
      calcularServico(item.servico, { ...contexto, quantidade: item.quantidade }),
    0,
  )
}