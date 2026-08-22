import MapComponent from './MapComponent'

export default function ProfessorProfile() {
  const rede = {
    nome: 'Rede Hoteleira',
    descricao: 'Sistema de gestão de hotéis desenvolvido pela Equipe Bravo.',
    atuacao: 'Gerenciamento de hotéis, cidades, quartos e reservas.'
  }

  const localizacoes = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        local: 'Fortaleza - CE',
        descricao: 'Cidade integrante da Rede Hoteleira.'
      },
      geometry: {
        type: 'Point',
        coordinates: [-38.5267, -3.7319]
      }
    },
    {
      type: 'Feature',
      properties: {
        local: 'Quixadá - CE',
        descricao: 'Cidade integrante da Rede Hoteleira.'
      },
      geometry: {
        type: 'Point',
        coordinates: [-39.0152, -4.9715]
      }
    },
    {
      type: 'Feature',
      properties: {
        local: 'Canoa Quebrada - CE',
        descricao: 'Cidade integrante da Rede Hoteleira.'
      },
      geometry: {
        type: 'Point',
        coordinates: [-37.7031, -4.5250]
      }
    }
  ]
}

  return (
    <section className="mb-5" id="informacoes-rede">
      <h2 className="text-secondary mb-3 fs-4">
        1. Informações da Rede
      </h2>

      <div className="card shadow-sm border-0 bg-light">
        <div className="card-body">
          <h5 className="card-title text-primary fw-bold">
            {rede.nome}
          </h5>

          <p className="card-text mb-2">
            <strong>Descrição:</strong> {rede.descricao}
          </p>

          <p className="card-text mb-0">
            <strong>Área de atuação:</strong> {rede.atuacao}
          </p>

          <MapComponent geojson={localizacoes} />
        </div>
      </div>
    </section>
  )
}