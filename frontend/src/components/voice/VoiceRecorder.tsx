import React, { useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Mic, Square, Loader2, AlertCircle } from "lucide-react";
import { speechService } from "@/services/speech.service";
import { cn } from "@/lib/utils";

type VoiceState = "idle" | "listening" | "processing" | "error" | "unavailable";

interface Props {
  onTranscript: (text: string) => void;
  language?: string;
}

export function VoiceRecorder({ onTranscript, language }: Props) {
  const { t } = useTranslation();
  const [state, setState] = useState<VoiceState>(
    typeof MediaRecorder === "undefined" ? "unavailable" : "idle"
  );
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState("");
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const start = useCallback(async () => {
    setError("");
    setTranscript("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setState("processing");
        try {
          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          const res = await speechService.transcribe(blob, language);
          if (res.text) {
            setTranscript(res.text);
            onTranscript(res.text);
            setState("idle");
          } else {
            setState("unavailable");
          }
        } catch {
          setError(t("voice.unavailable"));
          setState("error");
        }
      };
      recorder.start();
      mediaRef.current = recorder;
      setState("listening");
    } catch {
      setError(t("voice.error"));
      setState("error");
    }
  }, [language, onTranscript, t]);

  const stop = useCallback(() => {
    mediaRef.current?.stop();
  }, []);

  const label =
    state === "listening" ? t("voice.listening")
    : state === "processing" ? t("voice.processing")
    : state === "error" ? t("voice.error")
    : state === "unavailable" ? t("voice.unavailable")
    : t("voice.tap_to_speak");

  if (state === "unavailable") {
    return (
      <div className="flex items-center gap-2 text-sm"
           style={{ color: "hsl(var(--color-text-muted))" }}>
        <AlertCircle className="h-4 w-4 text-amber-500" aria-hidden />
        {t("voice.unavailable")}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3" role="region" aria-label="Voice recorder">
      <button
        onClick={state === "listening" ? stop : start}
        disabled={state === "processing"}
        className={cn(
          "flex h-16 w-16 items-center justify-center rounded-full transition-all",
          state === "listening"
            ? "bg-red-500 hover:bg-red-600 scale-110 shadow-lg"
            : "bg-blue-600 hover:bg-blue-700"
        )}
        aria-label={label}
        aria-pressed={state === "listening"}
      >
        {state === "processing" ? (
          <Loader2 className="h-7 w-7 text-white animate-spin" aria-hidden />
        ) : state === "listening" ? (
          <Square className="h-7 w-7 text-white" aria-hidden />
        ) : (
          <Mic className="h-7 w-7 text-white" aria-hidden />
        )}
      </button>

      <p className="text-sm text-center" style={{ color: "hsl(var(--color-text-muted))" }}>
        {label}
      </p>

      {transcript && (
        <div
          className="mt-1 max-w-sm rounded-lg border p-3 text-sm text-center"
          style={{ borderColor: "hsl(var(--color-border))", color: "hsl(var(--color-text))" }}
          role="status"
          aria-live="polite"
        >
          {transcript}
        </div>
      )}

      {error && (
        <p className="text-sm text-red-500" role="alert">{error}</p>
      )}
    </div>
  );
}
