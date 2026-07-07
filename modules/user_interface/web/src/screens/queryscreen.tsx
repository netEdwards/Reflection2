import { useState, useRef } from "react";
import type { Screen } from "../types/nav_types";
import './styles/main.css'
import type { QueryResult } from "../types/data_types";
import { getPywebviewApi } from "../pywebviewApi";
import { Header } from "../components/Header";

interface QueryScreenProps {
    onNavigate: (to: Screen) => void;
}

const QueryScreen = ({ onNavigate }: QueryScreenProps) => {
    const [inputText, setInputText] = useState<string>("");
    const [result, setResult] = useState<QueryResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null)

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const query = inputText?.trim();
        if (!query) return;

        const api = getPywebviewApi();
        if (!api){
            setError("Webview API not available...")
            return;
        }

        setLoading(true);
        setError(null);
        try{
            const res = await api.query(query, 5);
            setResult(res);
        }catch (err: any){
            console.error("Error running query", err);
            setError(err?.message ?? "Unknown error occured during query call.")
        }finally{
            setLoading(false);
        }
    }

    return (
        <section>
            <Header title="Query Current Data" onNavigate={onNavigate} />
            <div className="screen-content">
                <form onSubmit={handleSubmit} className="query-form">
                    <p>Input a natural language query that matches the language you have been using in your notes.</p>
                    <input
                        type="text"
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        placeholder="e.g. explain electromagnetic waves in my notes"
                        className="query-input"
                    />
                    <button type="submit" disabled={loading || !inputText.trim()}>
                        {loading ? "Searching" : "Run Query"}
                    </button>
                </form>

                {error && <p className="error-message">Error: {error}</p>}
                {result && (
                    <div className="query-results">
                    <h2>Results for: "{result.query}"</h2>
                    {result.results.length === 0 && <p>No results found.</p>}
                    <ul>
                        {result.results.map((r, idx) => (
                        <li key={idx} className="query-result-item">
                            <div className="result-header">
                            <strong>{r.document}</strong>
                            <span className="result-score">
                                score: {r.score.toFixed(4)}
                            </span>
                            </div>
                            {r.metadata?.heading_path && (
                            <div className="result-heading-path">
                                {r.metadata.heading_path}
                            </div>
                            )}
                            <pre className="result-text">{r.text}</pre>
                        </li>
                        ))}
                    </ul>
                    </div>
                )}
            </div>
        </section>
    )
}

export default QueryScreen;
