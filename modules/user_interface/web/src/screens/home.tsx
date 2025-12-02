
import type {Screen} from "../types/nav_types"
import './styles/main.css'
import logo from '../assets/reflection_identity.png' 
import { Button } from "../components/Button";

interface HomeScreenProps {
    onNavigate: (to: Screen) => void;
}

const Home = ({ onNavigate }: HomeScreenProps) => {
    return (
        <section className="home-screen">
            <h1 className="header">Welcome to Reflection</h1>
            <p className="normal_text">Your personal AI assistant for thoughtful reflection.</p>
            <img
                src={logo}
                className="main-image"
            />
            <div className="section_03_buttons">
                <button className="button_01" onClick={() => onNavigate("dataviewer")}>Data Viewer</button>
                <button className="button_01" onClick={() => onNavigate("queryscreen")}>Query Screen</button>
                <Button variant="primary" size="md" onClick={() => onNavigate("dataviewer")}>Test</Button>
            </div>
        </section>
    )
}

export default Home;