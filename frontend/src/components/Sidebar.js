import React, { useState } from "react";
import {
  FiUsers,
  FiCalendar,
  FiDollarSign,
  FiBarChart2,
  FiHelpCircle,
  FiLogOut,
  FiUser,
  FiClipboard,
  FiClock,
  FiFileText,
  FiSearch,
  FiTrendingUp,
  FiCheckCircle,
  FiUserPlus,
  FiSettings,
  FiCreditCard,
  FiEdit,
  FiAward,
} from "react-icons/fi";

const ROLE_LABELS = {
  super_admin: "Super Admin",
  hr_admin: "HR Admin",
  manager: "Manager",
  employee: "Employee",
};

const ADMIN_ROLES = ["super_admin", "hr_admin", "manager"];

export default function Sidebar({ user, onQuickAction, onLogout }) {
  const [leaveQuery, setLeaveQuery] = useState("");
  const [payrollQuery, setPayrollQuery] = useState("");
  const isAdmin = ADMIN_ROLES.includes(user?.role);

  const handleLeaveSearch = () => {
    const q = leaveQuery.trim();
    if (q) {
      onQuickAction(`Show leave records for ${q}`);
      setLeaveQuery("");
    }
  };

  const handlePayrollSearch = () => {
    const q = payrollQuery.trim();
    if (q) {
      onQuickAction(`Show payroll for ${q}`);
      setPayrollQuery("");
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>HRMS Agent</h2>
        <p className="sidebar-subtitle">AI-Powered HR Assistant</p>
      </div>

      {/* User profile section */}
      <div className="user-profile">
        <div className="user-avatar-sidebar">
          <FiUser size={18} />
        </div>
        <div className="user-info">
          <span className="user-name">{user?.name || "User"}</span>
          <span className="user-role">
            {ROLE_LABELS[user?.role] || user?.role || "Employee"}
          </span>
        </div>
      </div>

      {/* ── My Info ── */}
      <nav className="quick-actions">
        <h3>My Info</h3>
        <button
          className="quick-action-btn"
          onClick={() => onQuickAction(`Show my employee details`)}
        >
          <FiUser /> <span>My Profile</span>
        </button>
        <button
          className="quick-action-btn"
          onClick={() => onQuickAction(`Show my leave records`)}
        >
          <FiCalendar /> <span>My Leaves</span>
        </button>
        <button
          className="quick-action-btn"
          onClick={() => onQuickAction(`Show my attendance records`)}
        >
          <FiClock /> <span>My Attendance</span>
        </button>
        <button
          className="quick-action-btn"
          onClick={() => onQuickAction(`Show my payroll details`)}
        >
          <FiDollarSign /> <span>My Payroll</span>
        </button>
        <button
          className="quick-action-btn"
          onClick={() => onQuickAction(`Compare my tax under old vs new regime for my salary`)}
        >
          <FiTrendingUp /> <span>Tax Regime Compare</span>
        </button>
      </nav>

      {/* ── Search (for HR / Manager / Admin) ── */}
      {isAdmin && (
        <nav className="quick-actions">
          <h3>Search</h3>
          <div className="sidebar-search-group">
            <div className="sidebar-search-row">
              <input
                type="text"
                className="sidebar-search-input"
                placeholder="Name or EMP code"
                value={leaveQuery}
                onChange={(e) => setLeaveQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLeaveSearch()}
              />
              <button className="sidebar-search-btn" onClick={handleLeaveSearch} title="Search Leaves">
                <FiCalendar size={14} />
              </button>
            </div>
            <span className="sidebar-search-label">Leave Lookup</span>
          </div>
          <div className="sidebar-search-group">
            <div className="sidebar-search-row">
              <input
                type="text"
                className="sidebar-search-input"
                placeholder="Name or EMP code"
                value={payrollQuery}
                onChange={(e) => setPayrollQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handlePayrollSearch()}
              />
              <button className="sidebar-search-btn" onClick={handlePayrollSearch} title="Search Payroll">
                <FiDollarSign size={14} />
              </button>
            </div>
            <span className="sidebar-search-label">Payroll Lookup</span>
          </div>
        </nav>
      )}

      {/* ── Quick Actions ── */}
      <nav className="quick-actions">
        <h3>Quick Actions</h3>
        {isAdmin && (
          <button className="quick-action-btn highlight-btn" onClick={() => onQuickAction("__ADD_EMPLOYEE_FORM__")}>
            <FiUserPlus /> <span>Add Employee</span>
          </button>
        )}
        <button className="quick-action-btn" onClick={() => onQuickAction("Show me all employees")}>
          <FiUsers /> <span>All Employees</span>
        </button>
        <button className="quick-action-btn" onClick={() => onQuickAction("Compute salary breakup for 12 lakh CTC")}>
          <FiCreditCard /> <span>Salary Calculator</span>
        </button>
        {isAdmin && (
          <button className="quick-action-btn" onClick={() => onQuickAction("Show current HR policy")}>
            <FiSettings /> <span>HR Policy</span>
          </button>
        )}
        <button className="quick-action-btn" onClick={() => onQuickAction("What can you help me with?")}>
          <FiHelpCircle /> <span>Help</span>
        </button>
        <button className="quick-action-btn" onClick={() => onQuickAction("I want to request an update to my profile")}>
          <FiEdit /> <span>Update Request</span>
        </button>
      </nav>

      {/* ── Appraisals (Admin / HR / Manager) ── */}
      {isAdmin && (
        <nav className="quick-actions">
          <h3>Appraisals</h3>
          <button className="quick-action-btn" onClick={() => onQuickAction("Show all appraisal history")}>
            <FiAward /> <span>Appraisal History</span>
          </button>
          <button className="quick-action-btn" onClick={() => onQuickAction("Show all pending update requests")}>
            <FiEdit /> <span>Pending Updates</span>
          </button>
        </nav>
      )}

      {/* ── Reports (Admin / HR / Manager only) ── */}
      {isAdmin && (
        <nav className="quick-actions">
          <h3>Reports</h3>
          <button className="quick-action-btn" onClick={() => onQuickAction("Show company HR statistics")}>
            <FiBarChart2 /> <span>Company Stats</span>
          </button>
          <button className="quick-action-btn" onClick={() => onQuickAction("Show all pending leave requests")}>
            <FiClipboard /> <span>Pending Leaves</span>
          </button>
          <button className="quick-action-btn" onClick={() => onQuickAction("Show attendance summary for all employees")}>
            <FiClock /> <span>Attendance Summary</span>
          </button>
          <button className="quick-action-btn" onClick={() => onQuickAction("Show payroll summary for all employees for this month")}>
            <FiFileText /> <span>Payroll Summary</span>
          </button>
          <button className="quick-action-btn" onClick={() => onQuickAction("Show department wise employee count")}>
            <FiTrendingUp /> <span>Dept. Breakdown</span>
          </button>
          <button className="quick-action-btn" onClick={() => onQuickAction("Show all recently approved or rejected leaves")}>
            <FiCheckCircle /> <span>Leave Decisions</span>
          </button>
        </nav>
      )}

      <div className="sidebar-footer">
        <button className="logout-btn" onClick={onLogout}>
          <FiLogOut /> Sign Out
        </button>
        <p>Powered by GPT + FastAPI</p>
      </div>
    </aside>
  );
}
