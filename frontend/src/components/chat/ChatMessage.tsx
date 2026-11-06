import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Copy, Check, Bot, User } from "lucide-react";
import { SourceCitation } from "./SourceCitation";
import { MarkdownRenderer } from "../ui/MarkdownRenderer";
import type { ChatMessageRead, ChatTurnResponse, OfficialSource } from "@/types/api";
import { formatRelative, cn } from "@/lib/utils";

export type MessageData = (ChatMessageRead | (ChatTurnResponse & { id: string; created_at?: string })) & {
  streaming?: boolean;
};

interface Props {
  message: MessageData;
  sources?: OfficialSource[];
}

export function ChatMessage({ message, sources }: Props) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const copy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const officialSources: OfficialSource[] =
    sources ?? ("official_sources" in message ? (message.official_sources as OfficialSource[]) : []);

  return (
    <article
      className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}
      aria-label={isUser ? "Your message" : "Sahayak AI response"}
    >
      {/* Avatar */}
      <div
        className={cn(
          "mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-blue-600" : "bg-gradient-to-br from-teal-500 to-blue-600"
        )}
        aria-hidden
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-white" />
        )}
      </div>

      {/* Bubble */}
      <div className={cn("max-w-[78%] min-w-0", isUser ? "items-end" : "items-start", "flex flex-col gap-1")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "rounded-tr-sm text-white bg-blue-600"
              : "rounded-tl-sm"
          )}
          style={
            !isUser
              ? {
                  background: "hsl(var(--color-surface))",
                  color: "hsl(var(--color-text))",
                  border: "1px solid hsl(var(--color-border))",
                  boxShadow: "var(--shadow-sm)",
                }
              : undefined
          }
        >
          {/* Message content */}
          {message.streaming ? (
            <span className="flex items-center gap-2">
              <span style={{ whiteSpace: "pre-wrap" }}>{message.content}</span>
              <span className="flex gap-1" aria-label="Typing">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-current animate-bounce"
                    style={{ animationDelay: `${i * 150}ms` }}
                  />
                ))}
              </span>
            </span>
          ) : isUser ? (
            <span style={{ whiteSpace: "pre-wrap" }}>{message.content}</span>
          ) : (
            <MarkdownRenderer 
              content={message.content}
              className="prose-sm prose-p:leading-relaxed prose-headings:text-gray-900 prose-a:text-blue-600"
            />
          )}
        </div>

        {/* Sources for assistant messages */}
        {!isUser && officialSources.length > 0 && (
          <div className="w-full">
            <SourceCitation sources={officialSources} />
          </div>
        )}

        {/* Metadata row */}
        <div className={cn("flex items-center gap-2", isUser ? "flex-row-reverse" : "flex-row")}>
          {"created_at" in message && message.created_at && (
            <time
              className="text-[10px]"
              style={{ color: "hsl(var(--color-text-subtle))" }}
              dateTime={message.created_at}
            >
              {formatRelative(message.created_at)}
            </time>
          )}
          {"intent" in message && message.intent && !isUser && (
            <span
              className="text-[10px] font-medium px-1.5 py-0.5 rounded"
              style={{
                background: "hsl(var(--color-info-bg))",
                color: "hsl(var(--color-info))",
              }}
            >
              {message.intent.replace(/_/g, " ")}
            </span>
          )}
          {!isUser && !message.streaming && (
            <button
              onClick={copy}
              className="flex items-center gap-1 text-[10px] transition-colors hover:opacity-70"
              style={{ color: "hsl(var(--color-text-subtle))" }}
              aria-label={t("chat.copy")}
            >
              {copied ? (
                <Check className="h-3 w-3 text-green-500" aria-hidden />
              ) : (
                <Copy className="h-3 w-3" aria-hidden />
              )}
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
