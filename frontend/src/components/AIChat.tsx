import { Bot, Send, User, Loader2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import type { VideoMetadata, AIChatMessage } from "../types/api";
import { aiChat } from "../lib/api";

interface Props {
  videoContext?: VideoMetadata;
}

export function AIChat({ videoContext }: Props) {
  const [messages, setMessages] = useState<AIChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your video compression assistant. Ask me anything about codecs, compression settings, or how to get the best quality-to-size ratio.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const response = await aiChat(text, videoContext);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 flex flex-col h-96">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
        <Bot size={20} className="text-purple-600" />
        <h3 className="font-semibold text-gray-900 text-sm">AI Assistant</h3>
        {videoContext && (
          <span className="text-xs text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">
            Context: {videoContext.filename}
          </span>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <Bot
                size={20}
                className="text-purple-500 shrink-0 mt-1"
              />
            )}
            <div
              className={`max-w-xs rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {msg.content}
            </div>
            {msg.role === "user" && (
              <User
                size={20}
                className="text-blue-500 shrink-0 mt-1"
              />
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-2 items-center">
            <Bot size={20} className="text-purple-500" />
            <div className="bg-gray-100 rounded-lg px-3 py-2">
              <Loader2 size={16} className="animate-spin text-gray-400" />
            </div>
          </div>
        )}
      </div>

      <div className="px-4 py-3 border-t border-gray-100">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about video compression..."
            className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-300 focus:border-purple-400 outline-none"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white p-2 rounded-lg transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
