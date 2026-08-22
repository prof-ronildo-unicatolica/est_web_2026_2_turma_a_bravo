import ImageAndCarousel from '../components/ImageAndCarousel'
import ProfessorProfile from '../components/ProfessorProfile'
import DisciplinasList from '../components/DisciplinasList'
import StacksTable from '../components/StacksTable'
import VideoComponent from '../components/VideoComponent'
import InteractiveExamples from '../components/InteractiveExamples'

export default function Home() {
  return (
    <div className="mb-4">
      <h2 className="text-primary fw-bold">Bem-vindo à Rede Hoteleira</h2>
      <p className="text-secondary">
        Sistema de Gestão de Hotelaria desenvolvido na disciplina de Estágio II.
      </p>
      <ProfessorProfile />
      <DisciplinasList />
      <StacksTable />
      <ImageAndCarousel />
      <VideoComponent />
      <InteractiveExamples />
    </div>
  )
}
