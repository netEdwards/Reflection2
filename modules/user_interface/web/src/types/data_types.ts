// types.ts

export interface IngestSummary {
  files_processed: number;
  total_chunks: number;
  errors: string[];
}

export interface QueryResultChunk {
  document: string;
  text: string;
  score: number;
  metadata: Record<string, any>;
}

export interface QueryResult {
  query: string;
  results: QueryResultChunk[];
}

// pywebview API surface that JS expects
export interface PywebviewApi {
  ingest_file(path: string): Promise<IngestSummary>;
  ingest_directory(path: string): Promise<IngestSummary>;
  query(text: string, nResults?: number): Promise<QueryResult>;

  select_and_ingest_markdown_files(): Promise<IngestSummary>;
  select_and_ingest_markdown_folder(): Promise<IngestSummary>;
}
