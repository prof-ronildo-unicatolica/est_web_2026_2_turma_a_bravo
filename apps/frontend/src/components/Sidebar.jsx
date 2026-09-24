import { Link } from 'react-router-dom'

export default function Sidebar() {
  return (
    <div className="bg-dark text-white p-3 rounded shadow-sm h-100">
      <h5 className="text-primary fw-bold mb-4 border-bottom pb-2">Menu da Rede Hoteleira</h5>
      <ul className="nav nav-pills flex-column mb-auto">
        <li className="nav-item mb-2">
          <Link to="/" className="nav-link text-white">
            Início
          </Link>
        </li>
        <li className="nav-item mb-2">
          <Link to="/hoteis" className="nav-link text-white">
            Hotéis
          </Link>
        </li>
        <li className="nav-item mb-2">
          <Link to="/cidades" className="nav-link text-white">
            Cidades
          </Link>
        </li>
        <li className="nav-item mb-2">
          <Link to="/perfil" className="nav-link text-white">
            Perfil
          </Link>
        </li>
        <li className="nav-item mb-2">
          <Link to="/admin" className="nav-link text-white">
            Painel administrativo
          </Link>
        </li>
      </ul>
    </div>
  )
}
