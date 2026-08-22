import { useState } from 'react'

export default function InteractiveExamples() {
  const [selectedService, setSelectedService] = useState('hoteis')
  const [rating, setRating] = useState(0)
  const [submittedRating, setSubmittedRating] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [cityA, setCityA] = useState('Fortaleza - CE')
  const [cityB, setCityB] = useState('Quixadá - CE')

  const services = {
    hoteis: {
      title: 'Hotéis',
      desc: 'Consulte informações sobre os hotéis integrantes da rede hoteleira.',
      badge: 'Hospedagem'
    },
    quartos: {
      title: 'Quartos',
      desc: 'Consulte quartos e opções de acomodação disponíveis nos hotéis.',
      badge: 'Acomodações'
    },
    reservas: {
      title: 'Reservas',
      desc: 'Gerencie informações relacionadas às reservas dos clientes.',
      badge: 'Reservas'
    }
  }

  const cities = [
    { name: 'Fortaleza - CE', coords: [-38.5267, -3.7319] },
    { name: 'Quixadá - CE', coords: [-39.0152, -4.9715] },
    { name: 'Crateús - CE', coords: [-40.6728, -5.1764] },
    { name: 'Cedro - CE', coords: [-39.0625, -6.6074] },
    { name: 'Belo Horizonte - MG', coords: [-43.9378, -19.9191] },
    { name: 'São Paulo - SP', coords: [-46.6333, -23.5505] },
    { name: 'Rio de Janeiro - RJ', coords: [-43.1729, -22.9068] },
    { name: 'Florianópolis - SC', coords: [-48.548, -27.5954] },
    { name: 'Lisboa - PT', coords: [-9.1393, 38.7223] }
  ]

  const calculateDays = () => {
    if (!startDate || !endDate) return null

    const start = new Date(startDate)
    const end = new Date(endDate)
    const diff = end - start

    if (diff < 0) return 'Data de check-out inválida.'

    return Math.ceil(diff / (1000 * 60 * 60 * 24))
  }

  const calculateDistance = () => {
    const a = cities.find((city) => city.name === cityA)
    const b = cities.find((city) => city.name === cityB)

    if (!a || !b) return 0

    const [lon1, lat1] = a.coords
    const [lon2, lat2] = b.coords

    const toRad = (value) => (value * Math.PI) / 180
    const earthRadius = 6371

    const dLat = toRad(lat2 - lat1)
    const dLon = toRad(lon2 - lon1)

    const calc =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) *
        Math.cos(toRad(lat2)) *
        Math.sin(dLon / 2) ** 2

    const distance =
      2 * earthRadius * Math.atan2(Math.sqrt(calc), Math.sqrt(1 - calc))

    return distance.toFixed(1)
  }

  const days = calculateDays()

  return (
    <section className="mb-5" id="interactive-examples">
      <h2 className="text-secondary mb-3 fs-4">
        6. Recursos Interativos
      </h2>

      <p className="text-muted small">
        Recursos para consulta e interação com o Sistema de Gestão de Hotelaria.
      </p>

      <div className="row g-4">
        <div className="col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-header bg-dark text-white fw-bold">
              Consulta de Serviços
            </div>

            <div className="card-body">
              <label className="form-label fw-semibold">
                Selecione uma opção:
              </label>

              <select
                className="form-select mb-3"
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
              >
                <option value="hoteis">Hotéis</option>
                <option value="quartos">Quartos</option>
                <option value="reservas">Reservas</option>
              </select>

              <div className="p-3 bg-light rounded border">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <h5 className="text-primary fw-bold mb-0">
                    {services[selectedService].title}
                  </h5>

                  <span className="badge bg-info text-dark">
                    {services[selectedService].badge}
                  </span>
                </div>

                <p className="text-secondary small mb-0">
                  {services[selectedService].desc}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-header bg-dark text-white fw-bold">
              Avaliação da Rede Hoteleira
            </div>

            <div className="card-body text-center">
              <h5 className="text-primary fw-bold">
                Como você avalia nosso sistema?
              </h5>

              <p className="text-muted small">
                Selecione uma nota de 1 a 5 estrelas.
              </p>

              <div className="fs-2 mb-3">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className="btn border-0 p-1 fs-2"
                    onClick={() => {
                      setRating(star)
                      setSubmittedRating(false)
                    }}
                  >
                    {star <= rating ? '★' : '☆'}
                  </button>
                ))}
              </div>

              <p className="small text-secondary">
                {rating === 0
                  ? 'Escolha uma nota clicando nas estrelas.'
                  : `Você selecionou ${rating} estrela${rating > 1 ? 's' : ''}.`}
              </p>

              <button
                className="btn btn-primary"
                disabled={rating === 0}
                onClick={() => setSubmittedRating(true)}
              >
                Enviar Avaliação
              </button>

              {submittedRating && (
                <div className="alert alert-success mt-3 mb-0">
                  Obrigado pela sua avaliação!
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-header bg-dark text-white fw-bold">
              Período da Hospedagem
            </div>

            <div className="card-body">
              <p className="text-muted small">
                Informe as datas de check-in e check-out.
              </p>

              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label fw-semibold">
                    Check-in
                  </label>
                  <input
                    type="date"
                    className="form-control"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label fw-semibold">
                    Check-out
                  </label>
                  <input
                    type="date"
                    className="form-control"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </div>

              <div className="alert alert-info mt-3 mb-0">
                {!startDate || !endDate
                  ? 'Selecione as duas datas para calcular o período da hospedagem.'
                  : typeof days === 'number'
                    ? `Período da hospedagem: ${days} diária${days !== 1 ? 's' : ''}.`
                    : days}
              </div>
            </div>
          </div>
        </div>

        <div className="col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-header bg-dark text-white fw-bold">
              Distância entre Cidades
            </div>

            <div className="card-body">
              <p className="text-muted small">
                Compare a distância aproximada entre cidades da rede hoteleira.
              </p>

              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label fw-semibold">
                    Origem
                  </label>
                  <select
                    className="form-select"
                    value={cityA}
                    onChange={(e) => setCityA(e.target.value)}
                  >
                    {cities.map((city) => (
                      <option key={city.name} value={city.name}>
                        {city.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="col-md-6">
                  <label className="form-label fw-semibold">
                    Destino
                  </label>
                  <select
                    className="form-select"
                    value={cityB}
                    onChange={(e) => setCityB(e.target.value)}
                  >
                    {cities.map((city) => (
                      <option key={city.name} value={city.name}>
                        {city.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="alert alert-info mt-3 mb-0">
                Distância aproximada: <strong>{calculateDistance()} km</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}