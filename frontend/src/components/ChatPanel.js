import React, { useState, useRef, useEffect, useCallback } from "react";
import { FiSend } from "react-icons/fi";
import MessageBubble from "./MessageBubble";
import AddEmployeeForm from "./AddEmployeeForm";
import { sendMessage } from "../api";

export default function ChatPanel({ externalMessage, clearExternal, user }) {
  const [messages, setMessages] = useState([
    {
      role: "agent",
      content:
        "Hello! I'm your **HRMS Agent**. I can help you with:\n- Employee lookup\n- Leave management\n- Attendance records\n- Payroll details\n- Company statistics\n- **Salary breakup** from CTC (Indian labor laws)\n- **HR policy** configuration\n\nHow can I assist you today?",
      toolUsed: null,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const bottomRef = useRef(null);
  const externalHandled = useRef(false);

  const ADMIN_ROLES = ["super_admin", "hr_admin"];
  const isAdmin = user && ADMIN_ROLES.includes(user.role);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, showAddForm]);

  useEffect(() => {
    if (externalMessage && !externalHandled.current) {
      externalHandled.current = true;
      const doSend = async () => {
        const msg = externalMessage;
        clearExternal();

        // Intercept "Add Employee" sidebar button
        if (msg === "__ADD_EMPLOYEE_FORM__") {
          setShowAddForm(true);
          return;
        }

        setMessages((prev) => [...prev, { role: "user", content: msg, toolUsed: null }]);
        setLoading(true);
        try {
          const data = await sendMessage(msg);
          setMessages((prev) => [
            ...prev,
            { role: "agent", content: data.reply, toolUsed: data.tool_used },
          ]);
        } catch (err) {
          setMessages((prev) => [
            ...prev,
            {
              role: "agent",
              content: "Sorry, something went wrong. Please check if the backend is running.",
              toolUsed: null,
            },
          ]);
        } finally {
          setLoading(false);
        }
      };
      doSend();
    }
    if (!externalMessage) {
      externalHandled.current = false;
    }
  }, [externalMessage, clearExternal]);

  const handleSend = async (text) => {
    const msg = text || input.trim();
    if (!msg) return;

    setMessages((prev) => [...prev, { role: "user", content: msg, toolUsed: null }]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendMessage(msg);
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: data.reply, toolUsed: data.tool_used },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: "Sorry, something went wrong. Please check if the backend is running.",
          toolUsed: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEmployee = async (formData) => {
    setShowAddForm(false);
    // Send it as a natural language command to the agent
    const msg = `Add a new employee with the following details:\n- Employee Code: ${formData.emp_code}\n- Name: ${formData.name}\n- Email: ${formData.email}\n- Department: ${formData.department}\n- Designation: ${formData.designation}\n- Date of Joining: ${formData.date_of_joining}\n- Annual CTC: ₹${Number(formData.salary).toLocaleString("en-IN")}${formData.manager_name ? `\n- Manager: ${formData.manager_name}` : ""}`;

    setMessages((prev) => [...prev, { role: "user", content: msg, toolUsed: null }]);
    setLoading(true);

    try {
      const data = await sendMessage(msg);
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: data.reply, toolUsed: data.tool_used },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: "Sorry, something went wrong while adding the employee.",
          toolUsed: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <main className="chat-panel">
      <div className="chat-header">
        <h2>Chat with HRMS Agent</h2>
        {isAdmin && (
          <button
            className="btn-add-employee-header"
            onClick={() => setShowAddForm(true)}
            title="Add Employee"
          >
            + Add Employee
          </button>
        )}
      </div>

      <div className="messages-container">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} role={msg.role} content={msg.content} toolUsed={msg.toolUsed} />
        ))}

        {showAddForm && (
          <div className="message-row agent-row">
            <div className="bubble agent-bubble form-bubble">
              <AddEmployeeForm
                onSubmit={handleAddEmployee}
                onCancel={() => setShowAddForm(false)}
              />
            </div>
          </div>
        )}

        {loading && (
          <div className="message-row agent-row">
            <div className="avatar agent-avatar">
              <span className="dot-pulse" />
            </div>
            <div className="bubble agent-bubble typing-indicator">Thinking...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="input-bar">
        <input
          type="text"
          placeholder="Ask about employees, leave, payroll, salary breakup..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button onClick={() => handleSend()} disabled={loading || !input.trim()}>
          <FiSend size={20} />
        </button>
      </div>
    </main>
  );
}
