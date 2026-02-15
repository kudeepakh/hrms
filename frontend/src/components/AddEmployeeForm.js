import React, { useState, useEffect } from "react";
import { FiUserPlus, FiDollarSign, FiLoader } from "react-icons/fi";

const DEPARTMENTS = ["Engineering", "HR", "Finance", "Marketing", "Operations", "Sales", "Legal"];

export default function AddEmployeeForm({ onSubmit, onCancel }) {
  const [form, setForm] = useState({
    emp_code: "",
    name: "",
    email: "",
    department: "Engineering",
    designation: "",
    date_of_joining: new Date().toISOString().split("T")[0],
    salary: "",
    manager_name: "",
  });

  const [preview, setPreview] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  // Debounced salary preview
  useEffect(() => {
    if (!form.salary || isNaN(form.salary) || Number(form.salary) < 100000) {
      setPreview(null);
      return;
    }
    const timer = setTimeout(async () => {
      setLoadingPreview(true);
      try {
        const { salaryPreview } = await import("../api");
        const data = await salaryPreview(Number(form.salary));
        setPreview(data);
      } catch {
        setPreview(null);
      } finally {
        setLoadingPreview(false);
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [form.salary]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const validate = () => {
    const errs = {};
    if (!form.emp_code.trim()) errs.emp_code = "Required";
    if (!form.name.trim()) errs.name = "Required";
    if (!form.email.trim()) errs.email = "Required";
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = "Invalid email";
    if (!form.designation.trim()) errs.designation = "Required";
    if (!form.salary || isNaN(form.salary) || Number(form.salary) <= 0) errs.salary = "Enter valid CTC";
    if (!form.date_of_joining) errs.date_of_joining = "Required";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    const payload = { ...form, salary: Number(form.salary) };
    await onSubmit(payload);
    setSubmitting(false);
  };

  const fmt = (n) => (n != null ? `₹${Number(n).toLocaleString("en-IN")}` : "—");

  return (
    <div className="add-employee-form">
      <div className="form-header">
        <FiUserPlus size={20} />
        <h3>Add New Employee</h3>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label>Employee Code *</label>
            <input name="emp_code" value={form.emp_code} onChange={handleChange} placeholder="EMP006" />
            {errors.emp_code && <span className="form-error">{errors.emp_code}</span>}
          </div>

          <div className="form-group">
            <label>Full Name *</label>
            <input name="name" value={form.name} onChange={handleChange} placeholder="John Doe" />
            {errors.name && <span className="form-error">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label>Email *</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} placeholder="john@company.com" />
            {errors.email && <span className="form-error">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label>Department *</label>
            <select name="department" value={form.department} onChange={handleChange}>
              {DEPARTMENTS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Designation *</label>
            <input name="designation" value={form.designation} onChange={handleChange} placeholder="Software Engineer" />
            {errors.designation && <span className="form-error">{errors.designation}</span>}
          </div>

          <div className="form-group">
            <label>Date of Joining *</label>
            <input name="date_of_joining" type="date" value={form.date_of_joining} onChange={handleChange} />
            {errors.date_of_joining && <span className="form-error">{errors.date_of_joining}</span>}
          </div>

          <div className="form-group full-width">
            <label>Annual CTC (₹) *</label>
            <input name="salary" type="number" value={form.salary} onChange={handleChange} placeholder="1200000" min="0" />
            {errors.salary && <span className="form-error">{errors.salary}</span>}
          </div>

          <div className="form-group full-width">
            <label>Manager Name</label>
            <input name="manager_name" value={form.manager_name} onChange={handleChange} placeholder="Optional" />
          </div>
        </div>

        {/* Live salary preview */}
        {loadingPreview && (
          <div className="salary-preview loading">
            <FiLoader className="spin" size={16} /> Calculating breakup...
          </div>
        )}
        {preview && !loadingPreview && (
          <div className="salary-preview">
            <div className="preview-header">
              <FiDollarSign size={16} />
              <strong>Salary Breakup Preview</strong> (Monthly)
            </div>
            <div className="preview-grid">
              <div className="preview-item">
                <span>Basic</span><span>{fmt(preview?.breakup?.basic?.monthly)}</span>
              </div>
              <div className="preview-item">
                <span>HRA</span><span>{fmt(preview?.breakup?.hra?.monthly)}</span>
              </div>
              <div className="preview-item">
                <span>Special Allow.</span><span>{fmt(preview?.breakup?.special_allowance?.monthly)}</span>
              </div>
              <div className="preview-item">
                <span>PF (Employee)</span><span>{fmt(preview?.deductions?.pf_employee?.monthly)}</span>
              </div>
              <div className="preview-item">
                <span>Prof. Tax</span><span>{fmt(preview?.deductions?.professional_tax?.monthly)}</span>
              </div>
              <div className="preview-item">
                <span>TDS</span><span>{fmt(preview?.deductions?.tds?.monthly)}</span>
              </div>
              <div className="preview-item highlight">
                <span>Gross Salary</span><span>{fmt(preview?.gross_salary?.monthly)}</span>
              </div>
              <div className="preview-item highlight net">
                <span>Net Take-Home</span><span>{fmt(preview?.net_take_home?.monthly)}</span>
              </div>
            </div>
          </div>
        )}

        <div className="form-actions">
          <button type="button" className="btn-cancel" onClick={onCancel} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? "Adding..." : "Add Employee"}
          </button>
        </div>
      </form>
    </div>
  );
}
