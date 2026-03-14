"use client";

import {
  useState, useRef, useEffect,
  KeyboardEvent, FormEvent,
} from "react";
import {
  FileText, Send, Loader2, RotateCcw,
  Bot, User, AlertCircle, ChevronDown,
  Database, GitBranch,
} from "lucide-react";
import clsx from "clsx";
import { sendMessage, deleteSession } from "@/lib/api";
import type { Message } from "@/lib/api";
import MarkdownMessage from "./MarkdownMessage";

interface ChatScreenProps {
  sessionId: string;
  filename: string;
  deepTree: boolean;
  onReset: () => void;
}

function EngineBadge({ deepTree }: { deepTree: boolean }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full",
        deepTree
          ? "bg-violet-100 text-violet-600"
          : "bg-indigo-100 text-indigo-600"
      )}
    >
      {deepTree ? (
        <><GitBranch className="w-2.5 h-2.5" /> Deep Tree</>
      ) : (
        <><Database className="w-2.5 h-2.5" /> Vector DB</>
      )}
    </span>
  );
}

function TypingIndicator({ deepTree }: { deepTree: boolean }) {
  return (
    <div className="flex items-end gap-3 animate-fade-in">
      <div
        className={clsx(
          "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
          deepTree ? "bg-violet-100" : "bg-indigo-100"
        )}
        style={{ boxShadow: deepTree ? "0 2px 0 #ddd6fe" : "0 2px 0 #c7d2fe" }}
      >
        <Bot className={clsx("w-4 h-4", deepTree ? "text-violet-600" : "text-indigo-600")} />
      </div>
      <div className="bubble-assistant rounded-2xl rounded-bl-sm px-4 py-3">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-zinc-400 typing-dot animate-bounce-dot" />
          <span className="w-2 h-2 rounded-full bg-zinc-400 typing-dot animate-bounce-dot" />
          <span className="w-2 h-2 rounded-full bg-zinc-400 typing-dot animate-bounce-dot" />
        </div>
      </div>
    </div>
  );
}

function MessageBubble({
  message,
  deepTree,
}: {
  message: Message;
  deepTree: boolean;
}) {
  const isUser = message.role === "user";

  return (
    <div
      className={clsx(
        "flex items-end gap-3 animate-slide-up",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div
        className={clsx(
          "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
          isUser
            ? deepTree ? "bg-violet-600" : "bg-indigo-600"
            : deepTree ? "bg-violet-100" : "bg-indigo-100"
        )}
        style={
          isUser
            ? { boxShadow: deepTree ? "0 3px 0 #4c1d95" : "0 3px 0 #312e81" }
            : { boxShadow: deepTree ? "0 2px 0 #ddd6fe" : "0 2px 0 #c7d2fe" }
        }
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className={clsx("w-4 h-4", deepTree ? "text-violet-600" : "text-indigo-600")} />
        )}
      </div>

      <div
        className={clsx(
          "max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed",
          isUser
            ? deepTree
              ? "bubble-user-violet rounded-br-sm"
              : "bubble-user-indigo rounded-br-sm"
            : "bubble-assistant rounded-bl-sm"
        )}
      >
        <MarkdownMessage content={message.content} isUser={isUser} />
      </div>
    </div>
  );
}

export default function ChatScreen({
  sessionId,
  filename,
  deepTree,
  onReset,
}: ChatScreenProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `Hi! I've read **${filename}** and I'm ready to answer your questions. What would you like to know?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = (smooth = true) => {
    messagesEndRef.current?.scrollIntoView({
      behavior: smooth ? "smooth" : "instant",
    });
  };

  useEffect(() => { scrollToBottom(false); }, []);
  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  const handleScroll = () => {
    const el = scrollContainerRef.current;
    if (!el) return;
    setShowScrollBtn(el.scrollHeight - el.scrollTop - el.clientHeight > 200);
  };

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  }, [input]);

  const handleSend = async (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setIsLoading(true);

    try {
      const data = await sendMessage(sessionId, trimmed, deepTree);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get a response.");
      setMessages((prev) => prev.slice(0, -1));
      setInput(trimmed);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = async () => {
    await deleteSession(sessionId, deepTree).catch(() => {});
    onReset();
  };

  const accentFocus = deepTree
    ? "focus:border-violet-400 focus:ring-violet-100"
    : "focus:border-indigo-400 focus:ring-indigo-100";

  const sendBtnClass = deepTree ? "btn-3d-violet" : "btn-3d-indigo";

  return (
    <div className="flex flex-col h-screen page-bg">
      {/* Header */}
      <header
        className="shrink-0 bg-white border-b border-zinc-200 px-4 py-3 flex items-center justify-between z-10"
        style={{ boxShadow: "0 3px 0 #e4e4e7, 0 6px 20px rgba(0,0,0,0.06)" }}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div
            className={clsx(
              "w-9 h-9 rounded-xl flex items-center justify-center shrink-0",
              deepTree ? "bg-violet-100" : "bg-indigo-100"
            )}
            style={{ boxShadow: deepTree ? "0 2px 0 #ddd6fe" : "0 2px 0 #c7d2fe" }}
          >
            <FileText
              className={clsx(
                "w-5 h-5",
                deepTree ? "text-violet-600" : "text-indigo-600"
              )}
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-semibold text-zinc-900 text-sm truncate max-w-[160px] sm:max-w-xs md:max-w-sm">
                {filename}
              </p>
              <EngineBadge deepTree={deepTree} />
            </div>
            <p className="text-xs text-zinc-400">
              {messages.filter((m) => m.role === "user").length} message
              {messages.filter((m) => m.role === "user").length !== 1 ? "s" : ""} sent
            </p>
          </div>
        </div>

        <button
          onClick={handleNewChat}
          className="flex items-center gap-1.5 text-sm font-medium text-zinc-500 hover:text-zinc-800 hover:bg-zinc-100 px-3 py-1.5 rounded-lg transition-colors shrink-0"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          New Chat
        </button>
      </header>

      {/* Messages */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        <div className="max-w-2xl mx-auto flex flex-col gap-5">
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} deepTree={deepTree} />
          ))}
          {isLoading && <TypingIndicator deepTree={deepTree} />}

          {error && (
            <div
              className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-xl px-4 py-3 animate-fade-in"
              style={{ boxShadow: "0 2px 0 #fecaca" }}
            >
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollBtn && (
        <button
          onClick={() => scrollToBottom()}
          className="absolute bottom-24 right-6 w-9 h-9 rounded-full bg-white border border-zinc-200 flex items-center justify-center hover:bg-zinc-50 transition-all animate-fade-in"
          style={{ boxShadow: "0 3px 0 #e4e4e7, 0 6px 16px rgba(0,0,0,0.1)" }}
        >
          <ChevronDown className="w-4 h-4 text-zinc-600" />
        </button>
      )}

      {/* Input */}
      <div
        className="shrink-0 bg-white border-t border-zinc-200 px-4 py-4"
        style={{ boxShadow: "0 -3px 0 #e4e4e7 inset" }}
      >
        <form
          onSubmit={handleSend}
          className="max-w-2xl mx-auto flex items-end gap-3"
        >
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your document..."
              rows={1}
              disabled={isLoading}
              className={clsx(
                "w-full resize-none rounded-xl border px-4 py-3 text-sm leading-relaxed outline-none transition-all",
                "placeholder:text-zinc-400 bg-zinc-50 focus:bg-white focus:ring-2",
                accentFocus,
                isLoading
                  ? "border-zinc-200 text-zinc-400 cursor-not-allowed"
                  : "border-zinc-300 text-zinc-900"
              )}
              style={{ boxShadow: "inset 0 2px 6px rgba(0,0,0,0.04)" }}
            />
            <p className="absolute right-3 bottom-2.5 text-[10px] text-zinc-300 select-none">
              Enter ↵
            </p>
          </div>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={clsx(
              "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-150 shrink-0",
              input.trim() && !isLoading
                ? sendBtnClass
                : "bg-zinc-100 text-zinc-400 cursor-not-allowed border border-zinc-200"
            )}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
        <p className="max-w-2xl mx-auto text-center text-[11px] text-zinc-300 mt-2">
          Shift + Enter for new line · Enter to send
        </p>
      </div>
    </div>
  );
}
