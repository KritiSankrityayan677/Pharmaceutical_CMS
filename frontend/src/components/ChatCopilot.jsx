import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendChatThunk, appendUserMessage } from "../store/complaintSlice";

/**
 * AIVOA Copilot chat panel (right column).
 *
 * Features:
 *   - Drag-and-drop file zone at the top (also click-to-browse)
 *   - Scrolling chat history (user + assistant bubbles, PDF attachment card)
 *   - Extraction progress bar during LangGraph run
 *   - Text input at the bottom for follow-up corrections/questions
 *
 * All interactions flow through a single Redux thunk (sendChatThunk), which
 * calls POST /ai/chat on the backend.
 */
export default function ChatCopilot() {
  const dispatch = useDispatch();
  const { history, status, extractionProgress, lastIntent } = useSelector(
    (s) => s.complaint,
  );

  const [text, setText] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const scrollRef = useRef(null);

  const isLoading = status === "loading";

  // Auto-scroll chat to bottom on new message.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history, isLoading]);

  const send = ({ file }) => {
    const message = text.trim();
    if (!message && !file) return;
    dispatch(appendUserMessage({ text: message, fileName: file?.name }));
    dispatch(sendChatThunk({ message, file }));
    setText("");
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send({ file: null });
    }
  };

  const onFilePicked = (e) => {
    const f = e.target.files?.[0];
    if (f) send({ file: f });
    e.target.value = "";
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) send({ file: f });
  };

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div className="chat-header-left">
          <span className="chat-icon">🧪</span>
          <div>
            <div className="chat-title">AIVOA Copilot</div>
            <div className="chat-sub">Drop complaint files or paste text below.</div>
          </div>
        </div>
        <span className="beta-badge">BETA</span>
      </div>

      {/* Drop zone */}
      <div
        className={`dropzone ${isDragging ? "dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="dropzone-icon">⬆</div>
        <div>
          <b>Drag &amp; drop complaint document here</b>
          <div className="dropzone-sub">or <span className="link">click to browse</span></div>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.eml,.txt,.docx,.png,.jpg,.jpeg"
          onChange={onFilePicked}
          style={{ display: "none" }}
        />
      </div>
      <div className="format-note">
        <span>ⓘ</span> Supported formats: PDF, DOCX, TXT, EML &nbsp;·&nbsp; Max file size: 10MB
      </div>

      {/* Progress bar (only during extraction) */}
      {isLoading && lastIntent !== "update" && (
        <div className="progress-block">
          <div className="progress-header">
            <span>EXTRACTION PROGRESS</span>
            <span>{extractionProgress}%</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill indeterminate" />
          </div>
          <div className="progress-caption">
            Analyzing document content and extracting key details...
            <br />Please wait, this may take a few moments.
          </div>
        </div>
      )}

      {/* Chat scroll area */}
      <div className="chat-scroll" ref={scrollRef}>
        {history.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} />
        ))}
        {isLoading && <ChatBubble role="assistant" content="…" pending />}
      </div>

      {/* Composer */}
      <div className="composer">
        <button
          className="attach-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
          title="Attach a file"
        >
          📎
        </button>
        <input
          className="composer-input"
          placeholder="Type a message or paste a complaint..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={isLoading}
        />
        <button
          className="send-btn"
          onClick={() => send({ file: null })}
          disabled={isLoading || !text.trim()}
        >
          ➤
        </button>
      </div>
      <div className="disclaimer">
        AI responses may contain errors. Please verify information.
        <span className="powered">POWERED BY LANGGRAPH</span>
      </div>
    </div>
  );
}


function ChatBubble({ role, content, pending }) {
  const isUser = role === "user";
  // If a user message references an attachment, render a PDF card block.
  const attachmentMatch = isUser && content?.match(/\[Attached: ([^\]]+)\]/);
  const cleanText = attachmentMatch ? content.replace(/\n?\[Attached:[^\]]+\]/, "").trim() : content;
  return (
    <div className={`bubble-row ${isUser ? "user" : "assistant"}`}>
      {!isUser && <div className="avatar avatar-ai">✦</div>}
      <div className={`bubble ${isUser ? "bubble-user" : "bubble-assistant"} ${pending ? "pending" : ""}`}>
        {cleanText && <div className="bubble-text">{cleanText}</div>}
        {attachmentMatch && (
          <div className="attachment-card">
            <span className="attachment-icon">📄</span>
            <div>
              <div className="attachment-name">{attachmentMatch[1]}</div>
              <div className="attachment-sub">Document</div>
            </div>
          </div>
        )}
      </div>
      {isUser && <div className="avatar avatar-user">👤</div>}
    </div>
  );
}
