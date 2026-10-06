export default function Admin() {
  return (
    <div className="card shadow-sm">
      <div className="card-body p-4">
        <h2 className="mb-4">Área Administrativa</h2>

        <div className="alert alert-success">
          Acesso administrativo autorizado.
        </div>

        <p>
          Esta página é exclusiva para usuários administradores.
        </p>
      </div>
    </div>
  )
}