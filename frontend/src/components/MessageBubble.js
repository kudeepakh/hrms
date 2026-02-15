import React from "react";
import { FiUser, FiCpu } from "react-icons/fi";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MessageBubble({ role, content, toolUsed }) {
  const isUser = role === "user";

  return (
    <div className={`message-row ${isUser ? "user-row" : "agent-row"}`}>
      <div className={`avatar ${isUser ? "user-avatar" : "agent-avatar"}`}>
        {isUser ? <FiUser size={18} /> : <FiCpu size={18} />}
      </div>
      <div className={`bubble ${isUser ? "user-bubble" : "agent-bubble"}`}>
        {isUser ? (
          <p>{content}</p>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        )}
        {toolUsed && (
          <span className="tool-badge">Tool: {toolUsed}</span>
        )}
      </div>
    </div>
  );
}
