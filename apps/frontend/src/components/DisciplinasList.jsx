export default function DisciplinasList() {
  const servicos = [
    {
      nome: 'Gestão de Hotéis',
      descricao: 'Cadastro e consulta dos hotéis integrantes da rede.'
    },
    {
      nome: 'Gestão de Cidades',
      descricao: 'Cadastro e consulta das cidades atendidas pela rede hoteleira.'
    },
    {
      nome: 'Gestão de Quartos',
      descricao: 'Organização e consulta dos quartos disponíveis nos hotéis.'
    },
    {
      nome: 'Gestão de Reservas',
      descricao: 'Controle das reservas realizadas pelos clientes.'
    }
  ]

  return (
    <section className="mb-5" id="servicos-informacoes">
      <h2 className="text-secondary mb-3 fs-4">
        2. Serviços e Informações
      </h2>

      <p className="text-muted small">
        Principais serviços disponíveis no Sistema de Gestão de Hotelaria.
      </p>

      <div className="list-group shadow-sm border-0">
        {servicos.map((servico, idx) => (
          <div
            key={idx}
            className="list-group-item list-group-item-action border-1 rounded mb-2"
          >
            <h5 className="mb-1 text-primary fw-bold fs-5">
              {servico.nome}
            </h5>

            <p className="mb-1 mt-2 text-secondary small">
              {servico.descricao}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
