import './App.css';
import DataViewerScreen from './screens/dataviewer';
import Home from './screens/home'
import { useState } from "react";
import type {Screen} from "./types/nav_types"
import QueryScreen from './screens/QueryScreen';




export default function App() {
  const [screen, setScreen] = useState<Screen>("home");


  return (
    <div className="app-container">
      {screen === "home" && <Home onNavigate={setScreen} />}
      {screen === "dataviewer" && <DataViewerScreen onNavigate={setScreen} />}
      {screen === "queryscreen" && <QueryScreen onNavigate={setScreen} />}
    </div>
  );
}
