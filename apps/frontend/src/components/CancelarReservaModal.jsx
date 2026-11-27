import { useEffect } from 'react'
import { formatarDataHora, formatarDataIso, formatarValor } from '../utils/reservas'
import { montarAviso } from '../utils/cancelamento'

// estado: 'carregando' | 'pronto' | 'cancelando' | 'erro'
export default function CancelarReservaModal({
  codigo,
  descricao,
  reserva,
  estado,
  multa,
  erro,
  onConfirmar,
  onFechar,
}) {
  const ocupado = estado === 'carregando' || estado === 'cancelando'

  useEffect(() => {
    function aoTeclar(evento) {
      if (evento.key === 'Escape' && !ocupado) onFechar()
    }
    document.addEventListener('keydown', aoTeclar)
    return () => document.removeEventListener('keydown', aoTeclar)
  }, [ocupado, onFechar])

  const aviso = multa ? montarAviso(multa) : null

  return (
    <>
      <div
        className="modal fade show d-block"
        tabIndex="-1"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-cancelar-reserva"
      >
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title" id="titulo-cancelar-reserva">
                Cancelar reserva #{codigo}
              </h5>
              <button
                type="button"
                className="btn-close"
                aria-label="Fechar"
                onClick={onFechar}
                disabled={ocupado}
              />
            </div>

            <div className="modal-body">
              <p className="mb-1">
                <strong>{descricao.hotel}</strong> · {descricao.tipo}
              </p>
              <p className="text-muted mb-3">
                {formatarDataIso(reserva.data_entrada)} a {formatarDataIso(reserva.data_saida)} ·{' '}
                {formatarValor(reserva.valor_total)}
              </p>

              {estado === 'carregando' && (
                <div className="alert alert-info mb-0">Calculando a multa aplicável...</div>
              )}

              {aviso && (
                <>
                  <div className={`alert alert-${aviso.tipo}`} role="alert">
                    <div className="fw-semibold">{aviso.titulo}</div>
                    <div>{aviso.texto}</div>
                  </div>

                  <dl className="row mb-0 small">
                    <dt className="col-7">Cancelamento sem multa até</dt>
                    <dd className="col-5 text-end">
                      {multa.dataLimite ? formatarDataHora(multa.dataLimite) : '-'}
                    </dd>
                    <dt className="col-7">Valor da reserva</dt>
                    <dd className="col-5 text-end">{formatarValor(multa.valorTotal)}</dd>
                    <dt className="col-7">Multa ({Number(multa.percentualMulta) || 0}%)</dt>
                    <dd className="col-5 text-end">{formatarValor(multa.valorMulta)}</dd>
                    <dt className="col-7">Valor a reembolsar</dt>
                    <dd className="col-5 text-end fw-semibold">{formatarValor(multa.valorReembolso)}</dd>
                  </dl>
                </>
              )}

              {erro && (
                <div className="alert alert-danger mt-3 mb-0" role="alert">
                  {erro}
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button type="button" className="btn btn-outline-secondary" onClick={onFechar} disabled={ocupado}>
                Manter reserva
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={onConfirmar}
                disabled={!multa || ocupado}
              >
                {estado === 'cancelando' ? 'Cancelando...' : 'Confirmar cancelamento'}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop fade show" />
    </>
  )
}
