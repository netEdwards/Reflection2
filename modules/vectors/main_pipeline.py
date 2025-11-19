from modules.vectors.components.e_model import EmbeddingModel
from modules.vectors.components.parser import MarkdownNoteParser
from modules.vectors.components.chunker import chunk_elements
from pathlib import Path
import pandas as pd
import sys
import traceback

from modules.vectors.index.chroma_store import ChromaVectorStore
class InvalidMarkdownFileError(Exception):
    pass
class MarkdownParsingError(Exception):
    pass

class MarkdownChunkingError(Exception):
    pass

class pipeline:

    filename: str
    content: str
    path: Path


    def __init__(self, content):
        self.content = content
    
    def __init__(self, i_path):
        self.path       = i_path
        self._validate_path(self.path)
        self.content    = self.path.read_text(encoding="utf-8")
        if self.content == "" or None:
            raise InvalidMarkdownFileError(f"The file passed is empty or not readable at {self.path}. \nOutput content: {self.content}")
        
        self.filename   = self.path.name
        self.size       = self.path.stat().st_size
        self.stem       = self.path.stem
        self.last_mod   = self.path.stat().st_mtime
        self.create_at  = self.path.stat().st_ctime
        self.abs_path   = self.path.resolve()


        
        
        
        
    
    #Step 1 setup file and parse. 
    #DEBUGGING
    def process_input_file(self) -> pd.DataFrame:
        #call parser
        print("Starting pipeline for input file...")

        print(f"[DEBUGGING] Debugging information: ",
                f"Current file data: {self.content}"
                f"Current filename: {self.filename}"
            )
        try:
            p = self.path
            MdParser = MarkdownNoteParser()
            parsed_md = MdParser.parse_markdown_file(path=p)
            if parsed_md == None:
                raise MarkdownParsingError("The returned dictionary from the parser was empty or an error was thrown silently.")
            
            p_df = pd.DataFrame(parsed_md) #debugging use.
            
            
            chunked_md = chunk_elements(elements=parsed_md, doc_name=self.filename, doc_path=self.path)
            if chunked_md == None:
                raise MarkdownChunkingError("There was nothing returned from the chunking method or an error was thrown silently.")
            # Debugging | c_df = pd.DataFrame(chunked_md)
            
            
            text_embedder = EmbeddingModel(model_type="openai", model_name="text-embedding-3-small", batch_size=64)
            if text_embedder == None:
                raise ValueError("The embedding model failed to initialize.")
            
            texts = [c["text"] for c in chunked_md]
            vectors = text_embedder.embed(texts=texts)


            if len(vectors) != len(chunked_md):
                raise ValueError(
                    f"Embedding count mismatch: {len(vectors)} vectors for {len(chunked_md)} chunks"
                )
            
            for chunk, vec in zip(chunked_md, vectors):
                chunk["embeddings"] = vec
                
                
            store = ChromaVectorStore(
                collection_name="markdown_notes",
                persist_directory="./.chroma"
            )
            
            store.upsert_chunks(chunked_md)

            print(f"Pipeline completed successfully for file: {self.filename}")
            return chunked_md

        except Exception as e:
            print(f"There was an error while processing the file {e}:")
            traceback.print_exc()
    

    def _validate_path(self, path: Path):
        if not isinstance(path, Path):
            raise InvalidMarkdownFileError("Expected a pathlib.Path object.")
        if not path.exists():
            raise InvalidMarkdownFileError(f"Path does not exist: {path}")
        if not path.is_file():
            raise InvalidMarkdownFileError(f"Path is not a file: {path}")
        if path.suffix != ".md":
            raise InvalidMarkdownFileError(f"Only .md files are supported: {path.name}")