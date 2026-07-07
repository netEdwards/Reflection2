import type { Screen } from "../types/nav_types";

interface HeaderProps {
    title: string;
    onNavigate: (to: Screen) => void;
}

export const Header = ({ title, onNavigate }: HeaderProps) => (
    <div className="header">
        <h1>{title}</h1>
        <button onClick={() => onNavigate("home")} className="header-button">Home</button>
    </div>
);
