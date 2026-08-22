import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import Hoteis from './pages/Hoteis'
import Cidades from './pages/Cidades'

export default function App() {
  return (
    <div className="bg-light min-vh-100 pb-5">
      {/* Navbar de Exemplo */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm mb-4 sticky-top">
        <div className="container">
          <a className="navbar-brand d-flex align-items-center" href="#">
            <span className="fs-4 fw-bold text-primary">Rede Hoteleira</span>
            <span className="ms-2 badge bg-secondary text-wrap small">Estágio II</span>
          </a>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto">
              <li className="nav-item">
                <Link className="nav-link" to="/">Início</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/hoteis">Hotéis</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/cidades">Cidades</Link>
              </li>
            </ul>
            <div className="d-flex align-items-center gap-2">
              <button className="btn btn-outline-primary btn-sm px-3" type="button">
                Login
              </button>
              <button className="btn btn-primary btn-sm px-3" type="button">
                Perfil
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/hoteis" element={<Hoteis />} />
          <Route path="/cidades" element={<Cidades />} />
        </Routes>
      

        <footer className="mt-5 py-4 border-top text-center text-muted">
          <p className="mb-0">&copy; {new Date().getFullYear()} - Sistema de Gestão de Hotelaria. Desenvolvido pela Equipe Bravo.</p>        
        </footer>
      </div>
    </div>
  )
}
