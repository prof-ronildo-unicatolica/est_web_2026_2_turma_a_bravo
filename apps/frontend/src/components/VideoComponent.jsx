export default function VideoComponent() {
  return (
    <section className="mb-5" id="video-section">
      <h2 className="text-secondary mb-3 fs-4">
        5. Vídeo da Rede
      </h2>

      <p className="text-muted small">
        Espaço destinado à apresentação de vídeos relacionados à rede hoteleira.
      </p>

      <div className="card shadow-sm border-0 bg-white">
        <div className="card-header bg-dark text-white fw-bold d-flex align-items-center justify-content-between">
          <span>Conheça Nossa Rede Hoteleira</span>
          <span className="badge bg-primary">Vídeo</span>
        </div>

        <div className="card-body p-4">
          <div className="row g-4 align-items-center">

            <div className="col-lg-7">
              <div className="ratio ratio-16x9 bg-black rounded shadow-sm overflow-hidden border">
                <video controls preload="auto">
                  <source src="/hotel-quarto.mp4" type="video/mp4" />
                  Seu navegador não suporta a reprodução de vídeo.
                </video>
              </div>
            </div>

            <div className="col-lg-5">
              <h5 className="text-primary fw-bold mb-3">
                Experiência em Hospedagem
              </h5>

              <p className="text-secondary small">
                Conheça ambientes e serviços oferecidos pelos hotéis integrantes
                da nossa rede.
              </p>

              <p className="text-secondary small">
                O Sistema de Gestão de Hotelaria permite organizar informações
                sobre hotéis, cidades, quartos e reservas.
              </p>

              <div className="d-flex gap-2 mt-4">
                <span className="badge bg-light text-dark border">Hotéis</span>
                <span className="badge bg-light text-dark border">Quartos</span>
                <span className="badge bg-light text-dark border">Reservas</span>
              </div>
            </div>

          </div>
        </div>
      </div>
    </section>
  )
}