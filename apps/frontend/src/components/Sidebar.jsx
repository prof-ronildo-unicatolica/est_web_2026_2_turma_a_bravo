export default function Sidebar() {
  return (
    <div className="bg-dark text-white p-3 rounded shadow-sm h-100">
      <h5 className="text-primary fw-bold mb-4 border-bottom pb-2">Menu da Rede Hoteleira</h5>
      <ul className="nav nav-pills flex-column mb-auto">
        <li className="nav-item mb-2">
          <a href="#" className="nav-link text-white active" aria-current="page">
            Início
          </a>
        </li>
        <li className="nav-item mb-2">
          <a href="#professor-profile" className="nav-link text-white">
            1. Informações da Rede
          </a>
        </li>
        <li className="nav-item mb-2">
          <a href="#disciplinas-list" className="nav-link text-white">
            2. Serviços e Informações
          </a>
        </li>
        <li className="nav-item mb-2">
          <a href="#stacks-table" className="nav-link text-white">
            3. Tecnologias do Sistema
          </a>
        </li>
        <li className="nav-item mb-2">
          <a href="#image-carousel" className="nav-link text-white">
            4. Hotéis em Destaque
          </a>
        </li>
        <li className="nav-item mb-2">
          <a href="#video-section" className="nav-link text-white">
            5. Vídeo da Rede
          </a>
        </li>
        <li className="nav-item mb-2">
          <a href="#interactive-examples" className="nav-link text-white">
            6. Recursos Interativos
          </a>
        </li>
      </ul>
    </div>
  );
}
