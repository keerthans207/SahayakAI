import React, { useRef, useState, KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";
import { Send, Mic, Paperclip, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onSend: (text: string) => void;
  onVoice?: () => void;
  loading?: boolean;
  disabled?: boolean;
  voiceAvailable?: boolean;
  language?: string;
}

export function ChatComposer({ onSend, onVoice, loading, disabled, voiceAvailable }: Props) {
  const { t } = useTranslation();
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const text = value.trim();
    if (!text || loading || disabled) return;
    onSend(text);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const onInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  };

  return (
    <div
      className="flex items-end gap-2 rounded-2xl border p-2"
      style={{
        background: "hsl(var(--color-surface))",
        borderColor: "hsl(var(--color-border))",
        boxShadow: "var(--shadow-md)",
      }}
      role="group"
      aria-label="Message composer"
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKey}
        onInput={onInput}
        placeholder={t("chat.placeholder")}
        disabled={disabled || loading}
        rows={1}
        className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm focus:outline-none disabled:opacity-50"
        style={{ color: "hsl(var(--color-text))", maxHeight: "160px" }}
        aria-label={t("chat.placeholder")}
        aria-multiline="true"
      />
      <div className="flex items-center gap-1 pb-1">
        {voiceAvailable && (
          <button
            type="button"
            onClick={onVoice}
            disabled={disabled || loading}
            className="flex h-8 w-8 items-center justify-center rounded-lg transition-colors disabled:opacity-40"
            style={{
              background: "hsl(var(--color-surface-2))",
              color: "hsl(var(--color-text-muted))",
            }}
            aria-label={t("voice.tap_to_speak")}
          >
            <Mic className="h-4 w-4" aria-hidden />
          </button>
        )}
        <button
          type="button"
          onClick={submit}
          disabled={!value.trim() || disabled || loading}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
            value.trim() && !disabled && !loading
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "opacity-40"
          )}
          style={
            !value.trim() || disabled || loading
              ? { background: "hsl(var(--color-surface-2))", color: "hsl(var(--color-text-muted))" }
              : undefined
          }
          aria-label="Send message"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Send className="h-4 w-4" aria-hidden />
          )}
        </button>
      </div>
    </div>
  );
}
