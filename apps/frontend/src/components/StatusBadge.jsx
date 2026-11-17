import { infoStatus } from '../utils/reservas'

export default function StatusBadge({ status }) {
  const { rotulo, classe } = infoStatus(status)

  return <span className={`badge rounded-pill ${classe}`}>{rotulo}</span>
}