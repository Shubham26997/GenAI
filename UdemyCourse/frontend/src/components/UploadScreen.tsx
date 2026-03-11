"use client";

import { useState, useRef, useEffect, DragEvent, ChangeEvent } from "react";
import {
  FileText, Upload, Loader2, AlertCircle,
  Sparkles, CheckCircle2, Database, GitBranch, X,
  FileSpreadsheet, FileType,
} from "lucide-react";
import clsx from "clsx";
import { startChat } from "@/lib/api";

interface UploadScreenProps {
  deepTree: boolean;
  onDeepTreeToggle: () => void;
  onSessionStart: (sessionId: string, filename: string) => void;
}

type UploadStatus = "idle" | "uploading" | "success" | "error";

const ACCEPTED_EXTENSIONS = [".pdf", ".xlsx", ".xls", ".csv", ".docx", ".txt"];
const ACCEPT_ATTR = ACCEPTED_EXTENSIONS.join(",");

function FileIcon({ filename, className }: { filename: string; className?: string }) {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "xlsx" || ext === "xls")
    return <FileSpreadsheet className={className} />;
  if (ext === "csv" || ext === "txt" || ext === "docx")
    return <FileType className={className} />;
  return <FileText className={className} />;
}

function SuccessToast({ filename, deepTree }: { filename: string; deepTree: boolean }) {
  return (
    <div className="fixed top-5 left-1/2 -translate-x-1/2 z-50 animate-slide-up">
      <div className="flex items-center gap-3 bg-white border border-green-200 rounded-2xl px-5 py-3.5 min-w-[300px]"
        style={{ boxShadow: "0 4px 0 #bbf7d0, 0 10px 32px rgba(34,197,94,0.2)" }}>
        <div className="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center shrink-0">
          <CheckCircle2 className="w-5 h-5 text-green-600" />
        </div>
        <div>
          <p className="font-semibold text-zinc-800 text-sm">Upload successful!</p>
          <p className="text-zinc-400 text-xs mt-0.5 truncate max-w-[200px]">
            {filename} · {deepTree ? "PageIndex" : "Vector DB"}
          </p>
        </div>
      </div>
    </div>
  );
}

function DeepTreeToggle({ enabled, onToggle, disabled, deepTree }: {
  enabled: boolean;
  onToggle: () => void;
  disabled: boolean;
  deepTree: boolean;
}) {
  return (
    <div
      className={clsx(
        "flex items-center justify-between rounded-2xl px-4 py-3.5 transition-all duration-300 border",
        enabled
          ? "bg-violet-50 border-violet-200"
          : "bg-zinc-50 border-zinc-200"
      )}
      style={enabled ? { boxShadow: "0 2px 0 #ddd6fe, 0 4px 16px rgba(124,58,237,0.08)" } : { boxShadow: "0 2px 0 #e4e4e7, 0 4px 12px rgba(0,0,0,0.04)" }}
    >
      <div className="flex items-center gap-3">
        <div className={clsx(
          "w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-300",
          enabled ? "bg-violet-100" : "bg-zinc-100"
        )}>
          {enabled
            ? <GitBranch className="w-4 h-4 text-violet-600" />
            : <Database className="w-4 h-4 text-zinc-500" />
          }
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-zinc-800">Deep Tree</p>
            <span className={clsx(
              "text-[10px] font-bold px-1.5 py-0.5 rounded-full tracking-wide",
              enabled ? "bg-violet-200 text-violet-700" : "bg-zinc-200 text-zinc-500"
            )}>
              {enabled ? "ON" : "OFF"}
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            {enabled
              ? "PageIndex — LLM reasons through document tree"
              : "Vector DB — semantic similarity search"}
          </p>
        </div>
      </div>

      <button
        onClick={onToggle}
        disabled={disabled}
        className={clsx(
          "relative w-12 h-6 rounded-full transition-all duration-300 shrink-0 overflow-hidden",
          disabled && "opacity-40 cursor-not-allowed",
          enabled ? "toggle-violet" : "toggle-off"
        )}
      >
        <span className={clsx(
          "absolute top-0.5 w-5 h-5 bg-white rounded-full transition-all duration-300",
          "shadow-[0_1px_4px_rgba(0,0,0,0.25)]",
          enabled ? "left-[26px]" : "left-0.5"
        )} />
      </button>
    </div>
  );
}

export default function UploadScreen({ deepTree, onDeepTreeToggle, onSessionStart }: UploadScreenProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [successFilename, setSuccessFilename] = useState("");
  const [pendingSession, setPendingSession] = useState<{ id: string; filename: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (status !== "success" || !pendingSession) return;
    const t = setTimeout(() => onSessionStart(pendingSession.id, pendingSession.filename), 1800);
    return () => clearTimeout(t);
  }, [status, pendingSession, onSessionStart]);

  const handleFile = (file: File) => {
    setError(null);
    setStatus("idle");
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file type. Accepted: ${ACCEPTED_EXTENSIONS.join(", ")}`);
      return;
    }
    if (file.size > 50 * 1024 * 1024) { setError("File size must be under 50 MB."); return; }
    setSelectedFile(file);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setStatus("uploading");
    setError(null);
    try {
      const data = await startChat(selectedFile, deepTree);
      setSuccessFilename(data.filename);
      setStatus("success");
      setPendingSession({ id: data.session_id, filename: data.filename });
    } catch (err: unknown) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Something went wrong.");
    }
  };

  const isLocked = status === "uploading" || status === "success";
  const accentColor = deepTree ? "violet" : "indigo";

  return (
    <div className="page-bg min-h-screen flex flex-col items-center justify-center p-6">
      {status === "success" && <SuccessToast filename={successFilename} deepTree={deepTree} />}

      {/* Logo mark */}
      <div className="mb-8 animate-fade-in text-center">
        <div
          className={clsx(
            "inline-flex items-center justify-center w-16 h-16 rounded-3xl mb-4 transition-all duration-300",
            deepTree ? "bg-violet-600" : "bg-indigo-600"
          )}
          style={{ boxShadow: deepTree
            ? "0 6px 0 #5b21b6, 0 10px 32px rgba(124,58,237,0.35)"
            : "0 6px 0 #3730a3, 0 10px 32px rgba(79,70,229,0.35)"
          }}
        >
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">DocTalk</h1>
        <p className="mt-2 text-zinc-500">Drop any document. Ask anything. Instant answers.</p>
      </div>

      {/* Main card */}
      <div className="card-3d w-full max-w-lg p-7 animate-slide-up">
        <div className="space-y-4">
          {/* Engine toggle */}
          <DeepTreeToggle
            enabled={deepTree}
            onToggle={onDeepTreeToggle}
            disabled={isLocked}
            deepTree={deepTree}
          />

          {/* Upload zone */}
          <div
            onClick={() => !selectedFile && !isLocked && inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={clsx(
              "relative border-2 border-dashed rounded-2xl p-9 text-center transition-all duration-200",
              status === "success"
                ? "border-green-400 bg-green-50"
                : isDragging
                ? `border-${accentColor}-400 bg-${accentColor}-50 scale-[1.01] cursor-copy`
                : selectedFile
                ? `border-${accentColor}-300 bg-${accentColor}-50/50`
                : "border-zinc-200 bg-zinc-50/80 hover:border-zinc-300 hover:bg-white cursor-pointer"
            )}
            style={{ boxShadow: "inset 0 2px 8px rgba(0,0,0,0.03)" }}
          >
            <input ref={inputRef} type="file" accept={ACCEPT_ATTR} className="hidden"
              onChange={(e: ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />

            {status === "success" ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 rounded-2xl bg-green-100 flex items-center justify-center"
                  style={{ boxShadow: "0 4px 0 #bbf7d0" }}>
                  <CheckCircle2 className="w-7 h-7 text-green-600" />
                </div>
                <p className="font-semibold text-green-700">Uploaded successfully!</p>
                <p className="text-zinc-400 text-xs">Opening chat window...</p>
              </div>
            ) : selectedFile ? (
              <div className="flex flex-col items-center gap-3">
                <div
                  className={clsx("w-14 h-14 rounded-2xl flex items-center justify-center", deepTree ? "bg-violet-100" : "bg-indigo-100")}
                  style={{ boxShadow: deepTree ? "0 4px 0 #ddd6fe" : "0 4px 0 #c7d2fe" }}
                >
                  <FileIcon filename={selectedFile.name} className={clsx("w-7 h-7", deepTree ? "text-violet-600" : "text-indigo-600")} />
                </div>
                <div>
                  <p className="font-semibold text-zinc-800 text-sm truncate max-w-xs">{selectedFile.name}</p>
                  <p className="text-zinc-400 text-xs mt-0.5">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setError(null); setStatus("idle"); if (inputRef.current) inputRef.current.value = ""; }}
                  className="flex items-center gap-1 text-xs text-zinc-400 hover:text-red-500 transition-colors"
                >
                  <X className="w-3 h-3" /> Remove
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 rounded-2xl bg-white flex items-center justify-center border border-zinc-200"
                  style={{ boxShadow: "0 4px 0 #e4e4e7, 0 6px 16px rgba(0,0,0,0.05)" }}>
                  <Upload className="w-6 h-6 text-zinc-400" />
                </div>
                <div>
                  <p className="font-semibold text-zinc-700">Drop your document here</p>
                  <p className="text-zinc-400 text-sm mt-0.5">or <span className={clsx("font-medium", deepTree ? "text-violet-600" : "text-indigo-600")}>browse to choose a file</span></p>
                </div>
                <p className="text-xs text-zinc-400 bg-white border border-zinc-200 rounded-full px-3 py-1">
                  PDF · Excel · CSV · Word · TXT · up to 50 MB
                </p>
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-xl px-4 py-3 animate-fade-in"
              style={{ boxShadow: "0 2px 0 #fecaca" }}>
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* CTA Button */}
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isLocked}
            className={clsx(
              "w-full py-3.5 rounded-2xl font-semibold text-sm flex items-center justify-center gap-2 transition-all duration-150",
              status === "success"
                ? "btn-3d-green cursor-default"
                : selectedFile && !isLocked
                ? deepTree ? "btn-3d-violet" : "btn-3d-indigo"
                : "bg-zinc-100 text-zinc-400 cursor-not-allowed shadow-none border border-zinc-200"
            )}
          >
            {status === "uploading" ? (
              <><Loader2 className="w-4 h-4 animate-spin" />{deepTree ? "Building document tree..." : "Processing PDF..."}</>
            ) : status === "success" ? (
              <><CheckCircle2 className="w-4 h-4" />Opening chat...</>
            ) : (
              <>{deepTree ? <GitBranch className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}Start Chatting</>
            )}
          </button>

          <p className="text-center text-xs text-zinc-400">
            {deepTree
              ? "PageIndex builds a hierarchical tree from your document — no vector embeddings stored."
              : "Your document is chunked and embedded into Qdrant vector database."}
          </p>
        </div>
      </div>
    </div>
  );
}
