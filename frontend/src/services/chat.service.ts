import { api } from "./api";
import type {
  ChatSessionCreate,
  ChatSessionRead,
  ChatTurnCreate,
  ChatTurnResponse,
  ChatMessageRead,
} from "@/types/api";

export interface SessionWithMessages {
  session: ChatSessionRead;
  messages: ChatMessageRead[];
}

export const chatService = {
  createSession: (body: ChatSessionCreate) =>
    api.post<ChatSessionRead>("/api/v1/chat/sessions", body),

  getSession: (sessionId: string, signal?: AbortSignal) =>
    api.get<SessionWithMessages>(`/api/v1/chat/sessions/${sessionId}`, signal),

  sendMessage: (sessionId: string, body: ChatTurnCreate, signal?: AbortSignal) =>
    api.post<ChatTurnResponse>(
      `/api/v1/chat/sessions/${sessionId}/messages`,
      body,
      signal
    ),

  deleteSession: (sessionId: string) =>
    api.delete<void>(`/api/v1/chat/sessions/${sessionId}`),

  stream: (sessionId: string, body: ChatTurnCreate, signal?: AbortSignal) =>
    api.stream(`/api/v1/chat/sessions/${sessionId}/stream`, body, signal),
};
