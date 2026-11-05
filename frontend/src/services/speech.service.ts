import { api } from "./api";
import type { TranscribeResponse, SynthesizeRequest, SynthesizeResponse } from "@/types/api";

export const speechService = {
  transcribe: (audioBlob: Blob, language?: string, signal?: AbortSignal) => {
    const fd = new FormData();
    fd.append("file", audioBlob, "recording.webm");
    const path = language
      ? `/api/v1/speech/transcribe?language=${encodeURIComponent(language)}`
      : "/api/v1/speech/transcribe";
    return api.upload<TranscribeResponse>(path, fd, signal);
  },

  synthesize: (body: SynthesizeRequest, signal?: AbortSignal) =>
    api.post<SynthesizeResponse>("/api/v1/speech/synthesize", body, signal),
};
