import { useEffect, useState } from 'react'

const API = 'http://localhost:8000/api/v1'

export default function HoteisRaw() {
  const [hoteis, setHoteis] = useState(null)
  const [cidades, setCidades] = useState(null)
  const [erro, setErro] = useState(null)
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/cidades/`),
      fetch(`${API}/hoteis`),
    ])
      .then(async ([resCidades, resHoteis]) => {
        if (!resCidades.ok) throw new Error(`GET /cidades devolveu ${resCidades.status}`)
        if (!resHoteis.ok) throw new Error(`GET /hoteis devolveu ${resHoteis.status}`)
        return [await resCidades.json(), await resHoteis.json()]
      })
      .then(([jsonCidades, jsonHoteis]) => {
        setCidades(jsonCidades)
        setHoteis(jsonHoteis)
      })
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false))
  }, [])

  if (carregando) return <p>Carregando hoteis...</p>

  if (erro) {
    return (
      <div style={{ border: '1px solid red', padding: '1rem' }}>
        <strong>Erro ao falar com a API:</strong> {erro}
        <br />
        O backend esta no ar? Teste: <code>{API}/hoteis</code>
      </div>
    )
  }

  return (
    <section style={{ marginTop: '2rem' }}>
      <h2>Hoteis e Cidades — JSON bruto</h2>
      <p>
        Saida literal da API, sem tratamento. Serve para conferir que o dado
        atravessou banco → repository → service → rota → rede → navegador.
      </p>

      <h3>GET {API}/cidades/</h3>
      <pre style={{ background: '#f4f4f4', padding: '1rem', overflowX: 'auto' }}>
        {JSON.stringify(cidades, null, 2)}
      </pre>

      <h3>GET {API}/hoteis</h3>
      <pre style={{ background: '#f4f4f4', padding: '1rem', overflowX: 'auto' }}>
        {JSON.stringify(hoteis, null, 2)}
      </pre>
    </section>
  )
}