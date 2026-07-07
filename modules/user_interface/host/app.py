# modules/ui/host/app.py
from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
import json

import webview

from modules.orchestration.inference import ModelInterface
from modules.orchestration.sql.chatLogStore import ChatLogStore
from modules.vectors.VectorService import VectorService
from .window_ref import get_main_window, set_main_window

_vector_service: VectorService | None = None
_model_interface: ModelInterface | None = None

def get_vector_service() -> VectorService:
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service

def get_model_interface() -> ModelInterface:
    global _model_interface
    if _model_interface is None:
        _model_interface = ModelInterface(
            on_fragment=lambda data: get_main_window().evaluate_js(
                f"window._onChatFragment({json.dumps(data)})"
            )
        )
    return _model_interface

class JsApi:
    def __init__(self) -> None:
        pass
    
    # --- Ingestion ---------------------------------------------------
    
    def select_and_ingest_markdown_files(self) -> dict:
        """A method to open an Open dialog window with multi-select. This will allow the web interface to "select" the files. In reality PyWebview will select.
        
        Returns:
            dict: IngestSummary
        """
        window = get_main_window()
        
        if window is None:
            return {
                "files_processed": 0,
                "total_chunks": 0,
                "errors": ["No window attached to JsAPI."]
            }
            
        # open the OS file dialog
        file_types = (
            "Markdown files (*.md;*.markdown)",
            "All files (*.*)",
        )
        selected_paths = window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types,
        )
        #user cancels
        if not selected_paths:
            return {
                "files_processed": 0,
                "total_chunks": 0,
                "errors": ["No files selected."]
            }
            
        #begin to ingest each to VectorService
        summaries = []
        vectors = get_vector_service()
        for path in selected_paths:
            summary = vectors.ingest_file(path)
            summaries.append(summary)
            
        #combine summaries later
        files_processed = sum(s.files_processed for s in summaries)
        total_chunks = sum(s.total_chunks for s in summaries)
        errors = [err for s in summaries for err in s.errors]

        return {
            "files_processed": files_processed,
            "total_chunks": total_chunks,
            "errors": errors,
        }
        
    def select_and_ingest_markdown_folder(self) -> dict:
        """
        Open a folder picker, ingest all .md/.markdown files inside it.
        """
        window = get_main_window()
        if window is None:
            return {
                "files_processed": 0,
                "total_chunks": 0,
                "errors": ["No window attached to JsApi"],
            }

        folder = window.create_file_dialog(webview.FOLDER_DIALOG)
        if not folder:
            return {
                "files_processed": 0,
                "total_chunks": 0,
                "errors": ["No folder selected"],
            }

        folder_path = folder[0]  # pywebview returns a list
        vectors = get_vector_service()
        summary = vectors.ingest_directory(folder_path)
        return asdict(summary)

    def ingest_file(self, path: str) -> dict:
        """JS: window.pywebview.api.ingest_file(path)"""
        vectors = get_vector_service()
        summary = vectors.ingest_file(path)
        # IngestSummary is a dataclass, so asdict() makes it JSON-serializable
        return asdict(summary)

    def ingest_directory(self, path: str) -> dict:
        """JS: window.pywebview.api.ingest_directory(path)"""
        vectors = get_vector_service()
        summary = vectors.ingest_directory(path)
        return asdict(summary)

    # --- Query -------------------------------------------------------

    def query(self, text: str, nResults: int = 5) -> dict:
        """JS: window.pywebview.api.query(text, nResults)"""
        vectors = get_vector_service()
        result = vectors.query(query_text=text, n_results=nResults)
        # QueryResult has nested QueryResultChunk dataclasses :contentReference[oaicite:4]{index=4}
        return {
            "query": result.query,
            "results": [
                {
                    "document": r.document,
                    "text": r.text,
                    "score": r.score,
                    "metadata": r.metadata,
                }
                for r in result.results
            ],
        }

    # --- Model Interface -------------------------------------------------------
    
    def send_chat(self, prompt: str) -> dict:
        """Send a message to the orchestration interface, recieve a dictionary containing an endpoint or local models response. 

        Args:
            prompt (str): Clean string of users prompt.

        Returns:
            dict: Serialized message object from orchestration.
        """
        model_interface = get_model_interface()
        if not prompt:
            return {
                "error": "No prompt provided."
            }
            
        resp = model_interface.run_text(prompt)
        if not resp.text:
            return {
                "error": "There was an error with the response."
            }
        
        return {
            "id": resp.id,
            "identity": resp.identity,
            "text": resp.text,
            "timestamp": resp.timestamp.isoformat(),
        }
    
    def get_chats(self, t_from: str | None = None, t_to: str | None = None) -> dict:
        """A function to retrieve a set of messages from the sql database.
        Uses a time frame to retrieve a set of messages.
        You can pass `t_from` as None and then a `t_to` datatime to get present to a specific date.

        Args:
            t_from (str): ISO Format Datetime
            t_to (str): ISO Format Datetime

        Returns:
            dict: messages
        """
        chat_logger = ChatLogStore()
        messages = chat_logger.list_messages(t_from=t_from, t_to=t_to)
        return {
            "messages": [
                {
                    "id": m.id,
                    "identity": m.identity,
                    "text": m.text,
                    "timestamp": m.timestamp if isinstance(m.timestamp, str) else m.timestamp.isoformat(),
                }
                for m in messages
            ]
        }

def _get_web_url() -> str:
    """
    Dev: load Vite server (http://localhost:5173)
    Prod: load built dist/index.html as file:// URL
    """
    dev_url = os.getenv("REFLECTION_UI_DEV_URL", "http://localhost:5173/")
    if os.getenv("REFLECTION_UI_MODE", "dev") == "dev":
        return dev_url

    # Production: load built index.html
    here = Path(__file__).resolve().parent
    dist_index = here.parent / "web" / "dist" / "index.html"
    return dist_index.as_uri()


def main():
    api = JsApi()
    web_url = _get_web_url()

    window = webview.create_window(
        title="Reflection",
        url=web_url,
        js_api=api,
    )
    set_main_window(window)
    #api.window = window

    webview.start(debug=True)


if __name__ == "__main__":
    main()
