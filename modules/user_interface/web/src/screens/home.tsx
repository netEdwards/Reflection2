
import type {Screen} from "../types/nav_types"
import './styles/main.css'

interface HomeScreenProps {
    onNavigate: (to: Screen) => void;
}

const Home = ({ onNavigate }: HomeScreenProps) => {
    return (
        <section className="home-screen">
            <h1 className="header">Welcome to Reflection</h1>
            <p>Your personal AI assistant for thoughtful reflection.</p>
            <div>
                <button onClick={() => onNavigate("dataviewer")}>Data Viewer</button>
            </div>
        </section>
    )
}

export default Home;