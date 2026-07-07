import type { Screen } from "../types/nav_types"
import './styles/main.css'
import logo from '../assets/reflection_identity_web.png'
import { Button } from "../components/Button";

interface HomeScreenProps {
    onNavigate: (to: Screen) => void;
}

const Home = ({ onNavigate }: HomeScreenProps) => {
    return (
        <section className="home-screen">
            <div className="home-hero">
                <img src={logo} className="main-image" alt="Reflection" />
                <h1 className="home-title">Reflection</h1>
                <p className="normal_text">Your personal AI assistant for thoughtful reflection.</p>
                <div className="section_03_buttons">
                    <Button variant="primary" size="lg" onClick={() => onNavigate("chat")}>Chat</Button>
                    <Button variant="secondary" size="md" onClick={() => onNavigate("dataviewer")}>Data Viewer</Button>
                    <Button variant="secondary" size="md" onClick={() => onNavigate("queryscreen")}>Query Screen</Button>
                    <Button variant="secondary" size="sm" onClick={() => onNavigate("dataviewer")}>Test</Button>
                </div>
            </div>
        </section>
    )
}

export default Home;
