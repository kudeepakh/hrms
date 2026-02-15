import React, { useState } from "react";
import { FiMail, FiLock, FiUser, FiLogIn, FiUserPlus } from "react-icons/fi";
import { login, register, setToken, setStoredUser } from "../api";

export default function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let data;
      if (isRegister) {
        data = await register(name, email, password);
      } else {
        data = await login(email, password);
      }
      setToken(data.access_token);
      const userData = { name: data.name, email: data.email, role: data.role };
      setStoredUser(userData);
      onLogin(userData);
    } catch (err) {
      const msg =
        err.response?.data?.detail || "Something went wrong. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1>HRMS Agent</h1>
          <p>AI-Powered HR Management System</p>
        </div>

        <div className="login-tabs">
          <button
            className={`login-tab ${!isRegister ? "active" : ""}`}
            onClick={() => {
              setIsRegister(false);
              setError("");
            }}
          >
            <FiLogIn /> Sign In
          </button>
          <button
            className={`login-tab ${isRegister ? "active" : ""}`}
            onClick={() => {
              setIsRegister(true);
              setError("");
            }}
          >
            <FiUserPlus /> Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {isRegister && (
            <div className="input-group">
              <FiUser className="input-icon" />
              <input
                type="text"
                placeholder="Full Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="input-group">
            <FiMail className="input-icon" />
            <input
              type="email"
              placeholder="Email Address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="input-group">
            <FiLock className="input-icon" />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={4}
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="login-submit" disabled={loading}>
            {loading
              ? "Please wait..."
              : isRegister
              ? "Create Account"
              : "Sign In"}
          </button>
        </form>

        <div className="demo-credentials">
          <p><strong>Demo Accounts:</strong></p>
          <p>Admin: admin@hrms.com / admin123</p>
          <p>HR: priya.hr@company.com / hr123</p>
          <p>Manager: rahul.m@company.com / mgr123</p>
          <p>Employee: anita.d@company.com / emp123</p>
        </div>
      </div>
    </div>
  );
}
