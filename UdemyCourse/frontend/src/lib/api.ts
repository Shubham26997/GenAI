const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

function chatBase(deepTree: boolean): string {
  return deepTree ? `${BASE_URL}/pageindex/chat` : `${BASE_URL}/chat`;
}

export interface StartChatResponse {
  session_id: string;
  filename: string;
  message: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  session_id: string;
  filename: string;
  reply: string;
  history: Message[];
}

export async function startChat(
  file: File,
  deepTree: boolean
): Promise<StartChatResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${chatBase(deepTree)}/start`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to start chat session");
  }

  return res.json();
}

export async function sendMessage(
  sessionId: string,
  message: string,
  deepTree: boolean
): Promise<ChatResponse> {
  const res = await fetch(`${chatBase(deepTree)}/${sessionId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to send message");
  }

  return res.json();
}

export async function deleteSession(
  sessionId: string,
  deepTree: boolean
): Promise<void> {
  await fetch(`${chatBase(deepTree)}/${sessionId}`, { method: "DELETE" });
}
