import './App.css';
import DataViewerScreen from './screens/dataviewer';
import Home from './screens/home'
import { useState } from "react";
import type {Screen} from "./types/nav_types"
import QueryScreen from './screens/queryscreen';
import ChatScreen from './screens/chat';




export default function App() {
  const [screen, setScreen] = useState<Screen>("home");


  return (
    <div className="app-container">
      {screen === "home" && <Home onNavigate={setScreen} />}
      {screen === "dataviewer" && <DataViewerScreen onNavigate={setScreen} />}
      {screen === "queryscreen" && <QueryScreen onNavigate={setScreen} />}
      {screen === "chat" && <ChatScreen onNavigate={setScreen} />}
    </div>
  );
}
