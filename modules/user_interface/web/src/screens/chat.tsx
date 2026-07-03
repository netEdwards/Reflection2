import { useEffect, useRef, useState } from "react";
import type { Screen } from "../types/nav_types";
import './styles/main.css'
import type { ChatMessage } from "../types/data_types";
import { getPywebviewApi } from "../pywebviewApi";

interface ChatScreenProps {
    onNavigate: (to: Screen) => void;
}

// Qwen3 (and other reasoning models) wrap chain-of-thought in <think> tags.
// Strip it out for display; the raw text is still kept around per-message if we want to show it later.
function stripThinking(text: string): string {
    return text.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
}

const ChatScreen = ({ onNavigate }: ChatScreenProps) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputText, setInputText] = useState<string>("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const api = getPywebviewApi();
        if (!api) return;
        api.get_chats().then((res) => setMessages(res.messages)).catch((e) => {
            console.error("Error loading chat history:", e);
        });
    }, []);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    async function handleSend(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const prompt = inputText.trim();
        if (!prompt) return;

        const api = getPywebviewApi();
        if (!api) {
            setError("Webview API not available...");
            return;
        }

        const userMessage: ChatMessage = {
            id: `local-${Date.now()}`,
            identity: "user",
            text: prompt,
            timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setInputText("");
        setSending(true);
        setError(null);

        try {
            const res = await api.send_chat(prompt);
            if (res.error || !res.text) {
                setError(res.error ?? "No response from model.");
                return;
            }
            setMessages((prev) => [
                ...prev,
                {
                    id: res.id ?? `ai-${Date.now()}`,
                    identity: res.identity ?? "ai",
                    text: res.text!,
                    timestamp: res.timestamp ?? new Date().toISOString(),
                },
            ]);
        } catch (err: any) {
            console.error("Error sending chat message", err);
            setError(err?.message ?? "Unknown error occurred while sending message.");
        } finally {
            setSending(false);
        }
    }

    return (
        <section className="chat-screen">
            <div className="header">
                <h1>Chat</h1>
                <button onClick={() => onNavigate("home")} className="header-button">Home</button>
            </div>
            <div className="chat-messages">
                {messages.map((m) => (
                    <div key={m.id} className={`chat-message chat-message-${m.identity}`}>
                        <div className="chat-message-identity">{m.identity}</div>
                        <div className="chat-message-text">{stripThinking(m.text)}</div>
                    </div>
                ))}
                {sending && <div className="chat-message chat-message-ai chat-message-pending">Thinking...</div>}
                <div ref={bottomRef} />
            </div>
            {error && <p className="error-message">Error: {error}</p>}
            <form onSubmit={handleSend} className="chat-input-form">
                <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Ask something about your notes..."
                    className="chat-input"
                    disabled={sending}
                />
                <button type="submit" disabled={sending || !inputText.trim()}>
                    {sending ? "Sending" : "Send"}
                </button>
            </form>
        </section>
    );
};

export default ChatScreen;
