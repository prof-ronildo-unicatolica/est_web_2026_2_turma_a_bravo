import MapComponent from './MapComponent';

export default function HotelProfile({ hotel }) {
  if (!hotel) return null;

  return (
    <section className="mb-5" id="hotel-profile">
      <h2 className="text-secondary mb-3 fs-4">Detalhes do Hotel</h2>

      <div className="card shadow-sm border-0 bg-light">
        <div className="card-body">
          <h5 className="card-title text-primary fw-bold">
            {hotel.nome}
          </h5>

          <h6 className="card-subtitle mb-3 text-muted">
            {hotel.endereco}
          </h6>

          <p className="card-text mb-2">
            <strong>Classificação:</strong>{' '}
            <span className="badge bg-primary ms-1">
              {hotel.estrelas} estrelas
            </span>
          </p>

          <p className="card-text mb-0">
            <strong>Descrição:</strong> {hotel.descricao}
          </p>

          {hotel.localizacao && (
            <MapComponent geojson={hotel.localizacao} />
          )}
        </div>
      </div>
    </section>
  );
}
