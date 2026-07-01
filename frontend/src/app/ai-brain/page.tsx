"use client";

import { useEffect, useRef, useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Button, Textarea } from "@/components/Button";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface Conversation {
  id: number;
  title: string;
  created_at: string;
}

interface ChatResponse {
  conversation_id: number;
  answer: string;
  used_local_llm: boolean;
}

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  usedLocalLlm?: boolean;
}

export default function AiBrainPage() {
  const [conversationId, setConversationId] = useState<number | undefined>(
    undefined
  );
  const [continuingTitle, setContinuingTitle] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: conversations, refetch: refetchConversations } = usePolling(
    () => apiClient.get<Conversation[]>("/api/ai-brain/conversations"),
    [],
    { intervalMs: 30000 }
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, sending]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setSending(true);
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    try {
      const body: { conversation_id?: number; message: string } = {
        message: text,
      };
      if (conversationId !== undefined) body.conversation_id = conversationId;
      const res = await apiClient.post<ChatResponse>("/api/ai-brain/chat", body);
      setConversationId(res.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: res.answer,
          usedLocalLlm: res.used_local_llm,
        },
      ]);
      refetchConversations();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to get a response");
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startNewConversation = () => {
    setConversationId(undefined);
    setContinuingTitle(null);
    setMessages([]);
    setInput("");
    setError(null);
  };

  const continueConversation = (c: Conversation) => {
    setConversationId(c.id);
    setContinuingTitle(c.title);
    setMessages([]);
  };

  return (
    <PageShell
      title="AI Brain"
      description="Ask questions about your security posture, alerts, and compliance status"
      actions={
        <Button variant="secondary" onClick={startNewConversation}>
          New Conversation
        </Button>
      }
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <Card title="Conversations">
            <div className="flex flex-col gap-1 max-h-[60vh] overflow-y-auto scrollbar-thin">
              {!conversations || conversations.length === 0 ? (
                <div className="py-4 text-center text-xs text-slate-500">
                  No past conversations.
                </div>
              ) : (
                conversations.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => continueConversation(c)}
                    className={`rounded-md border px-3 py-2 text-left text-xs transition-colors ${
                      conversationId === c.id
                        ? "border-blue-500 bg-blue-600/10 text-slate-200"
                        : "border-[#1e2530] text-slate-400 hover:bg-[#11161d]"
                    }`}
                  >
                    <div className="truncate">{c.title}</div>
                    <div className="mt-0.5 text-slate-600">
                      {new Date(c.created_at).toLocaleString()}
                    </div>
                  </button>
                ))
              )}
            </div>
          </Card>
        </div>

        <div className="lg:col-span-3">
          <div className="flex h-[70vh] flex-col rounded-lg border border-[#1e2530] bg-[#0d1117]">
            {continuingTitle && (
              <div className="border-b border-[#1e2530] px-4 py-2 text-xs text-slate-500">
                Continuing conversation: <span className="text-slate-300">{continuingTitle}</span>
              </div>
            )}
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto scrollbar-thin p-4 flex flex-col gap-3"
            >
              {messages.length === 0 && (
                <div className="flex h-full items-center justify-center text-sm text-slate-600">
                  Ask a question to get started.
                </div>
              )}
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex ${
                    m.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
                      m.role === "user"
                        ? "bg-blue-600/20 text-slate-100"
                        : "bg-[#11161d] text-slate-200 border border-[#1e2530]"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{m.text}</div>
                    {m.role === "assistant" && (
                      <div className="mt-1.5">
                        <Badge variant={m.usedLocalLlm ? "low" : "medium"}>
                          {m.usedLocalLlm ? "Local LLM" : "Cloud LLM"}
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="max-w-[75%] rounded-lg border border-[#1e2530] bg-[#11161d] px-3 py-2 text-sm text-slate-500">
                    thinking...
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="border-t border-[#1e2530] px-4 py-2 text-xs text-red-400">
                {error}
              </div>
            )}

            <div className="flex items-end gap-2 border-t border-[#1e2530] p-3">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask the AI Brain about alerts, incidents, or compliance..."
                rows={2}
                disabled={sending}
                className="resize-none"
              />
              <Button onClick={sendMessage} disabled={sending || !input.trim()}>
                Send
              </Button>
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
