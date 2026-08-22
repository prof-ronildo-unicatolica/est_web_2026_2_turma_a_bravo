import HotelProfile from '../components/HotelProfile'

export default function Hoteis() {
  const hotelExemplo = {
  nome: 'Hotel Praia Azul',
  endereco: 'Fortaleza - CE',
  estrelas: 4,
  descricao: 'Hotel integrante da rede hoteleira.',
  localizacao: {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: {
          local: 'Hotel Praia Azul',
          descricao: 'Fortaleza - CE'
        },
        geometry: {
          type: 'Point',
          coordinates: [-38.5267, -3.7319]
        }
      }
    ]
  }
}

  return (
    <div className="mb-4">
      <h2 className="text-primary fw-bold">Hotéis</h2>
      <p className="text-secondary">
        Consulte os hotéis cadastrados na rede hoteleira.
      </p>

      <HotelProfile hotel={hotelExemplo} />
    </div>
  )
}
