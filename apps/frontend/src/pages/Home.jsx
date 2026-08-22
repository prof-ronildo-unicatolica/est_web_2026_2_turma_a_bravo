import ImageAndCarousel from '../components/ImageAndCarousel'

export default function Home() {
  return (
    <div className="mb-4">
      <h2 className="text-primary fw-bold">Bem-vindo à Rede Hoteleira</h2>
      <p className="text-secondary">
        Sistema de Gestão de Hotelaria desenvolvido na disciplina de Estágio II.
      </p>

      <ImageAndCarousel />
    </div>
  )
}
