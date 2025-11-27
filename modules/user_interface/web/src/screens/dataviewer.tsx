import { useRef, useState } from "react";
import type {Screen} from "../types/nav_types"
import { getPywebviewApi } from "../pywebviewApi";
import type { IngestSummary } from "../types/data_types";

interface DvScreenProps {
    onNavigate: (to: Screen) => void;
}

const DataViewerScreen = ({ onNavigate }: DvScreenProps) => {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [ingestResult, setIngestResult] = useState<IngestSummary | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    function handleClickSelectFile() {
        fileInputRef.current?.click();
    }

    async function handleIngestFiles(){
        const api = getPywebviewApi();
        if (!api) {
            setError("API not available. Try restarting");
        }

        setLoading(true);
        setError(null);
        try{
            const summary = await api?.select_and_ingest_markdown_files();
            setIngestResult(summary || null);
        } catch (e: any){
            console.error("Error ingesting files:", e);
            setError(e.message || "Unknown error during ingestion");
        } finally {
            setLoading(false);
        }
    }

    function handleFileChange(e: React.ChangeEvent<HTMLInputElement>){
        const files = e.target.files;
        if (!files || files.length === 0) return;

        const mdFiles = Array.from(files).filter(file => 
            file.name.toLowerCase().endsWith('.md') ||
            file.name.toLowerCase().endsWith('.markdown')
        );

        if (mdFiles.length === 0) {
            alert("Please select at least one markdown file (.md or .markdown).");
            return;
        }

        console.log("Selected markdown files:", mdFiles);
    }

    return (
        <section className="data-viewer-screen">
            <div className="header">
                <h1>Data Viewer</h1>
                <button onClick={() => onNavigate("home")} className="header-button">Home</button>
            </div>
            <div className="ingest-block">
                {loading ? (<p>Ingesting files, please wait...</p>) : (<h2>Ingest Markdown Files</h2>)}
                <button type="button" onClick={handleIngestFiles}>Select Files</button>
                {error && <p className="error-message">Error: {error}</p>}
                {ingestResult && (
                    <div style={{ marginTop: "1rem" }}>
                        <h3>Ingest summary</h3>
                        <p>Files processed: {ingestResult.files_processed}</p>
                        <p>Total chunks: {ingestResult.total_chunks}</p>
                        {ingestResult.errors.length > 0 && (
                        <>
                            <h4>Errors</h4>
                            <ul>
                            {ingestResult.errors.map((err, i) => (
                                <li key={i}>{err}</li>
                            ))}
                            </ul>
                        </>
                        )}
                    </div>
                )}
            </div>
        </section>
    )
};
export default DataViewerScreen;


