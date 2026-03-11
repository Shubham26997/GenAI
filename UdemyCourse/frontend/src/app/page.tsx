"use client";

import { useState } from "react";
import UploadScreen from "@/components/UploadScreen";
import ChatScreen from "@/components/ChatScreen";

interface Session {
  sessionId: string;
  filename: string;
  deepTree: boolean;
}

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [deepTree, setDeepTree] = useState(false);

  return session ? (
    <ChatScreen
      sessionId={session.sessionId}
      filename={session.filename}
      deepTree={session.deepTree}
      onReset={() => setSession(null)}
    />
  ) : (
    <UploadScreen
      deepTree={deepTree}
      onDeepTreeToggle={() => setDeepTree((v) => !v)}
      onSessionStart={(sessionId, filename) =>
        setSession({ sessionId, filename, deepTree })
      }
    />
  );
}
