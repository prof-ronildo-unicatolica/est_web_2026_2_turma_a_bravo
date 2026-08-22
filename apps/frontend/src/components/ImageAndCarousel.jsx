export default function ImageAndCarousel() {
  return (
    <section className="mb-5" id="image-carousel">
      <h2 className="text-secondary mb-4 fs-4">Hotéis em Destaque</h2>
      <div className="row g-4">
        {/* Image demonstration */}
        <div className="col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-header bg-dark text-white fw-bold">Conheça Nossa Rede Hoteleira</div>
            <div className="card-body d-flex flex-column justify-content-between">
              <p className="text-muted small">Conheça alguns dos hotéis e destinos disponíveis em nossa rede.</p>
              <img 
                src="/images/hotel-recepcao.png" 
                alt="Rede Hoteleira" 
                className="img-fluid rounded border shadow-sm mb-3"
              />
              <div className="small text-muted text-center">Conheça algumas opções de hospedagem da nossa rede</div>
            </div>
          </div>
        </div>

        {/* Carousel demonstration */}
        <div className="col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-header bg-dark text-white fw-bold">Destaques da Rede</div>
            <div className="card-body d-flex flex-column justify-content-between">
              <p className="text-muted small">Confira hotéis e destinos em destaque para sua próxima hospedagem.</p>
              
              <div id="hotelCarousel" className="carousel slide border rounded shadow-sm bg-light" data-bs-ride="carousel">
                <div className="carousel-indicators">
                  <button type="button" data-bs-target="#hotelCarousel" data-bs-slide-to="0" className="active" aria-current="true" aria-label="Slide 1"></button>
                  <button type="button" data-bs-target="#hotelCarousel" data-bs-slide-to="1" aria-label="Slide 2"></button>
                  <button type="button" data-bs-target="#hotelCarousel" data-bs-slide-to="2" aria-label="Slide 3"></button>
                  <button type="button" data-bs-target="#hotelCarousel" data-bs-slide-to="3" aria-label="Slide 4"></button>
                </div>
                <div className="carousel-inner" style={{ height: '220px' }}>
                  <div className="carousel-item active h-100">
                    <img 
                      src="/images/hotel-executivo.jpg" 
                      className="d-block w-100 h-100 rounded" 
                      alt="Hotel Executivo" 
                      style={{ objectFit: 'cover', filter: 'brightness(55%)' }}
                    />
                    <div className="carousel-caption d-block">
                      <h5>Hotel Executivo</h5>
                      <p className="small">Conforto e praticidade para viagens a trabalho.</p>
                    </div>
                  </div>
                  <div className="carousel-item h-100">
                    <img 
                      src="/images/hotel-praia.jpg" 
                      className="d-block w-100 h-100 rounded" 
                      alt="Hotel Praia" 
                      style={{ objectFit: 'cover', filter: 'brightness(55%)' }}
                    />
                    <div className="carousel-caption d-block">
                      <h5>Hotel Praia</h5>
                      <p className="small">Hospedagem próxima ao mar para lazer e descanso.</p>
                    </div>
                  </div>
                  <div className="carousel-item h-100">
                    <img 
                      src="/images/hotel-serra.jpg" 
                      className="d-block w-100 h-100 rounded" 
                      alt="Hotel Serra" 
                      style={{ objectFit: 'cover', filter: 'brightness(55%)' }}
                    />
                    <div className="carousel-caption d-block">
                      <h5>Hotel Serra</h5>
                      <p className="small">Tranquilidade e contato com a natureza.</p>
                    </div>
                  </div>
                  {/* Video slide */}
                  <div className="carousel-item h-100 bg-black">
                    <video 
                      className="d-block w-100 h-100 rounded" 
                      style={{ objectFit: 'contain' }} 
                      controls
                      muted
                      preload="auto"
                    >
                      <source src="/videos/hotel-quarto.mp4" type="video/mp4"/>
                      Seu navegador não suporta a reprodução de vídeos.
                    </video>
                    <div className="carousel-caption d-block bg-dark bg-opacity-75 rounded px-2 py-1" style={{ bottom: '10px' }}>
                      <h5 className="m-0 fs-6">Quarto de Hotel</h5>
                      <p className="small m-0" style={{ fontSize: '0.75rem' }}>Conforto e comodidade para uma boa hospedagem</p>
                    </div>
                  </div>
                </div>
                <button className="carousel-control-prev" type="button" data-bs-target="#hotelCarousel" data-bs-slide="prev">
                  <span className="carousel-control-prev-icon" aria-hidden="true"></span>
                  <span className="visually-hidden">Anterior</span>
                </button>
                <button className="carousel-control-next" type="button" data-bs-target="#hotelCarousel" data-bs-slide="next">
                  <span className="carousel-control-next-icon" aria-hidden="true"></span>
                  <span className="visually-hidden">Próximo</span>
                </button>
              </div>

              <div className="small text-muted text-center mt-3">Hotéis e destinos em destaque da nossa rede</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
