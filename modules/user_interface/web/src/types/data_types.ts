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

export interface ChatMessage {
  id: string;
  identity: string;
  text: string;
  timestamp: string;
}

export interface ChatResponse extends Partial<ChatMessage> {
  error?: string;
}

export interface GetChatsResult {
  messages: ChatMessage[];
}

// pywebview API surface that JS expects
export interface PywebviewApi {
  ingest_file(path: string): Promise<IngestSummary>;
  ingest_directory(path: string): Promise<IngestSummary>;
  query(text: string, nResults?: number): Promise<QueryResult>;

  select_and_ingest_markdown_files(): Promise<IngestSummary>;
  select_and_ingest_markdown_folder(): Promise<IngestSummary>;

  send_chat(prompt: string): Promise<ChatResponse>;
  get_chats(t_from?: string | null, t_to?: string | null): Promise<GetChatsResult>;
}
