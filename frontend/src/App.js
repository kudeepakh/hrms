import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatPanel from "./components/ChatPanel";
import LoginPage from "./components/LoginPage";
import { getToken, getStoredUser, clearToken } from "./api";
import "./App.css";

export default function App() {
  const [externalMessage, setExternalMessage] = useState(null);
  const [user, setUser] = useState(getToken() ? getStoredUser() : null);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    clearToken();
    setUser(null);
  };

  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="app-container">
      <Sidebar
        user={user}
        onQuickAction={(prompt) => setExternalMessage(prompt)}
        onLogout={handleLogout}
      />
      <ChatPanel
        externalMessage={externalMessage}
        clearExternal={() => setExternalMessage(null)}
        user={user}
      />
    </div>
  );
}
