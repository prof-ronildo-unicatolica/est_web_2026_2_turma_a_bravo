export default function StacksTable() {
  const tecnologias = [
    {
      area: 'Frontend',
      tecnologia: 'React + Vite',
      finalidade: 'Interface e páginas do sistema'
    },
    {
      area: 'Backend',
      tecnologia: 'FastAPI',
      finalidade: 'API e regras do sistema'
    },
    {
      area: 'Banco de Dados',
      tecnologia: 'PostgreSQL',
      finalidade: 'Armazenamento dos dados principais'
    },
    {
      area: 'Banco de Dados',
      tecnologia: 'MongoDB',
      finalidade: 'Dados utilizados em consultas específicas'
    },
    {
      area: 'Mensageria',
      tecnologia: 'RabbitMQ',
      finalidade: 'Comunicação e processamento de mensagens'
    },
    {
      area: 'Containers',
      tecnologia: 'Docker',
      finalidade: 'Execução dos serviços do projeto'
    }
  ]

  return (
    <section className="mb-5" id="tecnologias-sistema">
      <h2 className="text-secondary mb-3 fs-4">
        3. Tecnologias do Sistema
      </h2>

      <p className="text-muted small">
        Principais tecnologias utilizadas no Sistema de Gestão de Hotelaria.
      </p>

      <div className="table-responsive shadow-sm rounded">
        <table className="table table-bordered table-striped table-hover mb-0 bg-white">
          <thead className="table-dark">
            <tr>
              <th>Área</th>
              <th>Tecnologia</th>
              <th>Finalidade</th>
            </tr>
          </thead>

          <tbody>
            {tecnologias.map((item, idx) => (
              <tr key={idx}>
                <td className="fw-bold text-primary">
                  {item.area}
                </td>
                <td className="fw-semibold">
                  {item.tecnologia}
                </td>
                <td>
                  {item.finalidade}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}