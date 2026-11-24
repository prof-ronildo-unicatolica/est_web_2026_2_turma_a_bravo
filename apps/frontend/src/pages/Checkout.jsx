import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { apiFetch } from '../services/api'
import {
  calcularCotacao,
  calcularServico,
  calcularTotalServicos,
  formatarMoeda,
  paraBasisPoints,
  paraCentavos,
  pessoasParaServicos,
} from '../utils/precificacao'

const ROTULO_COBRANCA = {
  por_pessoa_dia: 'por pessoa/dia',
  por_diaria: 'por diária',
  por_servico: 'por serviço',
}

function formatarData(dataIso) {
  return dataIso.split('-').reverse().join('/')
}

function rotuloAjuste(ajusteBp) {
  const percentual = (ajusteBp / 100).toLocaleString('pt-BR')
  return `${ajusteBp > 0 ? '+' : ''}${percentual}%`
}

export default function Checkout() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [hoteis, setHoteis] = useState([])
  const [quartos, setQuartos] = useState([])
  const [tarifas, setTarifas] = useState([])
  const [servicos, setServicos] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erroApi, setErroApi] = useState('')

  const [hotelId, setHotelId] = useState(searchParams.get('hotel') || '')
  const [quartoId, setQuartoId] = useState('')
  const [checkIn, setCheckIn] = useState('')
  const [checkOut, setCheckOut] = useState('')
  const [adultos, setAdultos] = useState(1)
  const [idadesCriancas, setIdadesCriancas] = useState([])
  const [horarioCheckin, setHorarioCheckin] = useState('')
  const [horarioCheckout, setHorarioCheckout] = useState('')
  const [naoReembolsavel, setNaoReembolsavel] = useState(false)
  const [servicosEscolhidos, setServicosEscolhidos] = useState({})
  const [enviando, setEnviando] = useState(false)
  const [erroEnvio, setErroEnvio] = useState('')

  useEffect(() => {
    async function carregar() {
      try {
        const [listaHoteis, listaQuartos, listaTarifas] = await Promise.all([
          apiFetch('/hoteis'),
          apiFetch('/quartos'),
          apiFetch('/tarifas-temporada'),
        ])
        setHoteis(listaHoteis)
        setQuartos(listaQuartos)
        setTarifas(listaTarifas)
      } catch {
        setErroApi('Não foi possível carregar hotéis, quartos e tarifas.')
      } finally {
        setCarregando(false)
      }
    }

    carregar()
  }, [])

  useEffect(() => {
    if (!hotelId) {
      setServicos([])
      return undefined
    }

    let ativo = true

    apiFetch(`/servicos-adicionais?hotel_id=${hotelId}`)
      .then((lista) => {
        if (ativo) setServicos(lista)
      })
      .catch(() => {
        if (ativo) setErroApi('Não foi possível carregar os serviços adicionais.')
      })

    return () => {
      ativo = false
    }
  }, [hotelId])

  const hotelSelecionado = hoteis.find((hotel) => hotel.id === hotelId)
  const hoteisDisponiveis = hoteis.filter((hotel) => hotel.status !== 'Inativo')
  const quartosDoHotel = quartos.filter((quarto) => quarto.hotel_id === hotelId)
  const quarto = quartosDoHotel.find((item) => item.id === quartoId)
  const tarifasDoHotel = tarifas
    .filter((tarifa) => tarifa.hotel_id === hotelId)
    .map((tarifa) => ({
      nome: tarifa.nome,
      dataInicio: tarifa.data_inicio,
      dataFim: tarifa.data_fim,
      ajusteBp: paraBasisPoints(tarifa.percentual_ajuste),
    }))

  const idades = idadesCriancas.map((valor) => (valor === '' ? Number.NaN : Number(valor)))

  const { erros, cotacao } = calcularCotacao({
    precoDiariaCentavos: quarto ? paraCentavos(quarto.preco_diaria) : 0,
    checkIn,
    checkOut,
    adultos: Number(adultos),
    idadesCriancas: idades,
    naoReembolsavel,
    horarioCheckin: horarioCheckin || null,
    horarioCheckout: horarioCheckout || null,
    tarifasTemporada: tarifasDoHotel,
    maxAdultos: quarto ? quarto.max_adultos : null,
    maxCriancas: quarto ? quarto.max_criancas : null,
  })

  const contextoServicos = {
    noites: cotacao ? cotacao.noites : 0,
    pessoas: pessoasParaServicos(Number(adultos) || 0, idades),
  }

  const servicosSelecionados = servicos
    .filter((servico) => servicosEscolhidos[servico.id] !== undefined)
    .map((servico) => ({ servico, quantidade: servicosEscolhidos[servico.id] }))

  const totalServicos = calcularTotalServicos(servicosSelecionados, contextoServicos)
  const totalGeral = (cotacao ? cotacao.total : 0) + totalServicos
  async function confirmarReserva() {
    setEnviando(true)
    setErroEnvio('')
    try {
      const reserva = await apiFetch('/reservas', {
        method: 'POST',
        body: JSON.stringify({
          quarto_id: quartoId,
          data_entrada: checkIn,
          data_saida: checkOut,
          quantidade_adultos: Number(adultos),
          idades_criancas: idades,
          nao_reembolsavel: naoReembolsavel,
          horario_checkin: horarioCheckin || null,
          horario_checkout: horarioCheckout || null,
        }),
      })
      navigate(`/reservas/${reserva.id}`)
    } catch (e) {
      setErroEnvio(e.message)
      setEnviando(false)
    }
  }

  const hoje = new Date().toLocaleDateString('en-CA')

  const tarifasNoPeriodo = tarifasDoHotel.filter(
    (tarifa) => checkIn && checkOut && tarifa.dataInicio < checkOut && tarifa.dataFim >= checkIn,
  )

  function alterarHotel(novoId) {
    setHotelId(novoId)
    setQuartoId('')
    setServicosEscolhidos({})
  }

  function adicionarCrianca() {
    setIdadesCriancas((atual) => [...atual, ''])
  }

  function removerCrianca(indice) {
    setIdadesCriancas((atual) => atual.filter((_, posicao) => posicao !== indice))
  }

  function alterarIdade(indice, valor) {
    setIdadesCriancas((atual) =>
      atual.map((idade, posicao) => (posicao === indice ? valor : idade)),
    )
  }

  function alternarServico(servicoId) {
    setServicosEscolhidos((atual) => {
      const copia = { ...atual }
      if (copia[servicoId] !== undefined) {
        delete copia[servicoId]
      } else {
        copia[servicoId] = 1
      }
      return copia
    })
  }

  function alterarQuantidade(servicoId, valor) {
    const quantidade = Math.max(1, Number(valor) || 1)
    setServicosEscolhidos((atual) => ({ ...atual, [servicoId]: quantidade }))
  }

  if (carregando) {
    return <div className="alert alert-info">Carregando checkout...</div>
  }

  return (
    <div className="admin-panel">
      <div className="mb-4">
        <span className="admin-badge">Reserva</span>
        <h2 className="mb-1 mt-3">Checkout</h2>
        <p className="mb-0 text-secondary">
          Escolha o quarto, as datas, a tarifa e os serviços. O total é atualizado na hora.
        </p>
      </div>

      {erroApi && <div className="alert alert-warning">{erroApi}</div>}

      <div className="row g-4 align-items-start">
        <div className="col-lg-7">
          <div className="card shadow-sm admin-card mb-4">
            <div className="card-body p-4">
              <h4 className="mb-3">1. Hotel e quarto</h4>

              <div className="mb-3">
                <label className="form-label" htmlFor="checkout-hotel">Hotel</label>
                <select
                  id="checkout-hotel"
                  className="form-select"
                  value={hotelId}
                  onChange={(evento) => alterarHotel(evento.target.value)}
                >
                  <option value="">Selecione o hotel</option>
                  {hoteisDisponiveis.map((hotel) => (
                    <option key={hotel.id} value={hotel.id}>{hotel.nome}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-label" htmlFor="checkout-quarto">Quarto</label>
                <select
                  id="checkout-quarto"
                  className="form-select"
                  value={quartoId}
                  onChange={(evento) => setQuartoId(evento.target.value)}
                  disabled={!hotelId}
                >
                  <option value="">
                    {hotelId && quartosDoHotel.length === 0
                      ? 'Este hotel ainda não tem quartos'
                      : 'Selecione o quarto'}
                  </option>
                  {quartosDoHotel.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.tipo} - {formatarMoeda(paraCentavos(item.preco_diaria))} por pessoa/noite
                      (até {item.max_adultos} adulto(s) e {item.max_criancas} criança(s))
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="card shadow-sm admin-card mb-4">
            <div className="card-body p-4">
              <h4 className="mb-3">2. Datas e hóspedes</h4>

              <div className="row g-3 mb-3">
                <div className="col-sm-6">
                  <label className="form-label" htmlFor="checkout-checkin">Check-in</label>
                  <input
                    id="checkout-checkin"
                    type="date"
                    className="form-control"
                    min={hoje}
                    value={checkIn}
                    onChange={(evento) => setCheckIn(evento.target.value)}
                  />
                </div>
                <div className="col-sm-6">
                  <label className="form-label" htmlFor="checkout-checkout">Check-out</label>
                  <input
                    id="checkout-checkout"
                    type="date"
                    className="form-control"
                    min={checkIn || hoje}
                    value={checkOut}
                    onChange={(evento) => setCheckOut(evento.target.value)}
                  />
                </div>
              </div>

              <div className="row g-3 mb-3">
                <div className="col-sm-6">
                  <label className="form-label" htmlFor="checkout-chegada">
                    Horário de chegada (opcional)
                  </label>
                  <input
                    id="checkout-chegada"
                    type="time"
                    className="form-control"
                    value={horarioCheckin}
                    onChange={(evento) => setHorarioCheckin(evento.target.value)}
                  />
                  <div className="form-text">Padrão: 14:00. Antes disso há taxa de early check-in.</div>
                </div>
                <div className="col-sm-6">
                  <label className="form-label" htmlFor="checkout-saida">
                    Horário de saída (opcional)
                  </label>
                  <input
                    id="checkout-saida"
                    type="time"
                    className="form-control"
                    value={horarioCheckout}
                    onChange={(evento) => setHorarioCheckout(evento.target.value)}
                  />
                  <div className="form-text">Padrão: 12:00. Depois disso há taxa de late check-out.</div>
                </div>
              </div>

              <div className="mb-3">
                <label className="form-label" htmlFor="checkout-adultos">Adultos</label>
                <input
                  id="checkout-adultos"
                  type="number"
                  className="form-control"
                  min={1}
                  max={quarto ? quarto.max_adultos : undefined}
                  value={adultos}
                  onChange={(evento) => setAdultos(evento.target.value)}
                />
              </div>

              <div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="form-label mb-0">Crianças</span>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-primary"
                    onClick={adicionarCrianca}
                  >
                    Adicionar criança
                  </button>
                </div>

                {idadesCriancas.length === 0 && (
                  <div className="form-text">Nenhuma criança adicionada.</div>
                )}

                {idadesCriancas.map((idade, indice) => (
                  <div className="input-group mb-2" key={indice}>
                    <span className="input-group-text">Criança {indice + 1}</span>
                    <input
                      type="number"
                      className="form-control"
                      min={0}
                      max={17}
                      placeholder="Idade (0 a 17)"
                      value={idade}
                      onChange={(evento) => alterarIdade(indice, evento.target.value)}
                    />
                    <button
                      type="button"
                      className="btn btn-outline-danger"
                      onClick={() => removerCrianca(indice)}
                    >
                      Remover
                    </button>
                  </div>
                ))}
                <div className="form-text">
                  Até 2 anos não paga; de 3 a 12 paga 50%; de 13 a 17 paga como adulto.
                </div>
              </div>
            </div>
          </div>

          <div className="card shadow-sm admin-card mb-4">
            <div className="card-body p-4">
              <h4 className="mb-3">3. Tarifa</h4>

              <div className="form-check mb-2">
                <input
                  id="tarifa-flexivel"
                  type="radio"
                  name="tarifa"
                  className="form-check-input"
                  checked={!naoReembolsavel}
                  onChange={() => setNaoReembolsavel(false)}
                />
                <label className="form-check-label" htmlFor="tarifa-flexivel">
                  <strong>Flexível</strong> - reembolsável, sem desconto
                </label>
              </div>

              <div className="form-check mb-3">
                <input
                  id="tarifa-nao-reembolsavel"
                  type="radio"
                  name="tarifa"
                  className="form-check-input"
                  checked={naoReembolsavel}
                  onChange={() => setNaoReembolsavel(true)}
                />
                <label className="form-check-label" htmlFor="tarifa-nao-reembolsavel">
                  <strong>Não reembolsável</strong> - 10% de desconto nas diárias
                </label>
              </div>

              {tarifasNoPeriodo.length > 0 && (
                <div className="alert alert-info mb-0">
                  <div className="fw-semibold mb-1">Tarifas de temporada no seu período</div>
                  {tarifasNoPeriodo.map((tarifa) => (
                    <div key={`${tarifa.nome}-${tarifa.dataInicio}`}>
                      {tarifa.nome}: {rotuloAjuste(tarifa.ajusteBp)} de {formatarData(tarifa.dataInicio)} a{' '}
                      {formatarData(tarifa.dataFim)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="card shadow-sm admin-card">
            <div className="card-body p-4">
              <h4 className="mb-3">4. Serviços adicionais</h4>

              {!hotelId && <div className="text-secondary">Selecione um hotel para ver os serviços.</div>}

              {hotelId && servicos.length === 0 && (
                <div className="text-secondary">Este hotel não tem serviços adicionais.</div>
              )}

              {servicos.map((servico) => {
                const selecionado = servicosEscolhidos[servico.id] !== undefined
                const valorServico = selecionado
                  ? calcularServico(servico, {
                      ...contextoServicos,
                      quantidade: servicosEscolhidos[servico.id],
                    })
                  : 0

                return (
                  <div className="border rounded p-3 mb-2" key={servico.id}>
                    <div className="d-flex justify-content-between align-items-start gap-3">
                      <div className="form-check">
                        <input
                          id={`servico-${servico.id}`}
                          type="checkbox"
                          className="form-check-input"
                          checked={selecionado}
                          onChange={() => alternarServico(servico.id)}
                        />
                        <label className="form-check-label" htmlFor={`servico-${servico.id}`}>
                          <span className="fw-semibold">{servico.nome}</span>
                          {servico.descricao && (
                            <span className="d-block text-secondary small">{servico.descricao}</span>
                          )}
                        </label>
                      </div>

                      <div className="text-end">
                        <div>{formatarMoeda(paraCentavos(servico.preco))}</div>
                        <div className="small text-secondary">{ROTULO_COBRANCA[servico.tipo_cobranca]}</div>
                      </div>
                    </div>

                    {selecionado && (
                      <div className="d-flex justify-content-between align-items-center mt-2">
                        {servico.tipo_cobranca === 'por_servico' ? (
                          <div className="d-flex align-items-center gap-2">
                            <label className="small mb-0" htmlFor={`quantidade-${servico.id}`}>
                              Quantidade
                            </label>
                            <input
                              id={`quantidade-${servico.id}`}
                              type="number"
                              className="form-control form-control-sm"
                              style={{ width: '80px' }}
                              min={1}
                              value={servicosEscolhidos[servico.id]}
                              onChange={(evento) => alterarQuantidade(servico.id, evento.target.value)}
                            />
                          </div>
                        ) : (
                          <span className="small text-secondary">
                            {contextoServicos.noites} noite(s)
                            {servico.tipo_cobranca === 'por_pessoa_dia' &&
                              ` x ${contextoServicos.pessoas} pessoa(s)`}
                          </span>
                        )}
                        <strong>{formatarMoeda(valorServico)}</strong>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <div className="col-lg-5">
          <div className="card shadow-sm admin-card position-sticky" style={{ top: '80px' }}>
            <div className="card-body p-4">
              <h4 className="mb-3">Resumo e total</h4>

              {hotelSelecionado && (
                <div className="mb-3">
                  <div className="fw-semibold">{hotelSelecionado.nome}</div>
                  {quarto && <div className="text-secondary small">{quarto.tipo}</div>}
                </div>
              )}

              {erros.length > 0 && (
                <ul className="text-secondary small ps-3">
                  {erros.map((erro) => (
                    <li key={erro}>{erro}</li>
                  ))}
                </ul>
              )}

              {cotacao && (
                <div>
                  <div className="d-flex justify-content-between mb-1">
                    <span>
                      Diárias ({cotacao.noites} noite(s), {cotacao.adultos} adulto(s)
                      {cotacao.criancasPagantes > 0 && `, ${cotacao.criancasPagantes} criança(s) pagante(s)`}
                      {cotacao.bebes > 0 && `, ${cotacao.bebes} bebê(s)`})
                    </span>
                    <span>{formatarMoeda(cotacao.subtotalDiarias)}</span>
                  </div>

                  {cotacao.taxaEarlyCheckin > 0 && (
                    <div className="d-flex justify-content-between mb-1">
                      <span>Early check-in</span>
                      <span>{formatarMoeda(cotacao.taxaEarlyCheckin)}</span>
                    </div>
                  )}

                  {cotacao.taxaLateCheckout > 0 && (
                    <div className="d-flex justify-content-between mb-1">
                      <span>Late check-out</span>
                      <span>{formatarMoeda(cotacao.taxaLateCheckout)}</span>
                    </div>
                  )}

                  {cotacao.descontoNaoReembolsavel > 0 && (
                    <div className="d-flex justify-content-between mb-1 text-success">
                      <span>Desconto não reembolsável</span>
                      <span>- {formatarMoeda(cotacao.descontoNaoReembolsavel)}</span>
                    </div>
                  )}

                  {servicosSelecionados.length > 0 && (
                    <div className="d-flex justify-content-between mb-1">
                      <span>Serviços adicionais</span>
                      <span>{formatarMoeda(totalServicos)}</span>
                    </div>
                  )}

                  <details className="my-3">
                    <summary className="small text-secondary">Ver valor de cada noite</summary>
                    <ul className="list-unstyled small mb-0 mt-2">
                      {cotacao.detalheNoites.map((noite) => (
                        <li className="d-flex justify-content-between" key={noite.data}>
                          <span>
                            {formatarData(noite.data)}
                            {noite.nomeTarifa && (
                              <span className="badge bg-warning-subtle text-dark ms-2">
                                {noite.nomeTarifa} {rotuloAjuste(noite.ajusteBp)}
                              </span>
                            )}
                          </span>
                          <span>{formatarMoeda(noite.valor)}</span>
                        </li>
                      ))}
                    </ul>
                  </details>
                </div>
              )}

              <hr />

              <div className="d-flex justify-content-between align-items-center">
                <span className="fs-5">Total</span>
                <span className="fs-3 fw-bold text-primary">{formatarMoeda(totalGeral)}</span>
              </div>

              <button
                type="button"
                className="btn btn-primary w-100 mt-3"
                disabled={!cotacao || enviando}
                onClick={confirmarReserva}
              >
                {enviando ? 'Enviando...' : 'Confirmar reserva'}
              </button>

              {totalServicos > 0 && (
                <div className="alert alert-warning mt-3 mb-0 small">
                  Os serviços adicionais ainda não são enviados ao servidor: o valor da reserva
                  considera só as diárias e taxas.
                </div>
              )}

              {erroEnvio && <div className="alert alert-danger mt-3 mb-0">{erroEnvio}</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}