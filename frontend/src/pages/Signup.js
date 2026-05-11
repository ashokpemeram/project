import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signup as signupRequest } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { validateAlphaName, validateEmail } from "../utils/validation";
import "./Auth.css";

export default function Signup() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    const nextErrors = {};
    const nameError = validateAlphaName(name, "Full name");
    if (nameError) nextErrors.name = nameError;
    const emailError = validateEmail(email);
    if (emailError) nextErrors.email = emailError;
    if (!String(password ?? "").trim()) nextErrors.password = "Password is required.";
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      return;
    }

    setLoading(true);
    try {
      const data = await signupRequest({ name: name.trim(), email: email.trim(), password });
      login({ token: data.token, user: data.user });
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card card fade-up">
        <div className="auth-header">
          <h1>Create Doctor Account</h1>
          <p>Start protecting patient scans with secure imaging.</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Full name
            <input
              type="text"
              value={name}
              className={fieldErrors.name ? "input-error" : ""}
              onChange={(e) => {
                setName(e.target.value);
                if (fieldErrors.name) {
                  setFieldErrors((prev) => ({ ...prev, name: "" }));
                }
                if (error) setError("");
              }}
              required
            />
            {fieldErrors.name && <div className="field-error">{fieldErrors.name}</div>}
          </label>
          <label>
            Email
            <input
              type="email"
              value={email}
              className={fieldErrors.email ? "input-error" : ""}
              onChange={(e) => {
                setEmail(e.target.value);
                if (fieldErrors.email) {
                  setFieldErrors((prev) => ({ ...prev, email: "" }));
                }
                if (error) setError("");
              }}
              required
            />
            {fieldErrors.email && <div className="field-error">{fieldErrors.email}</div>}
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              className={fieldErrors.password ? "input-error" : ""}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) {
                  setFieldErrors((prev) => ({ ...prev, password: "" }));
                }
                if (error) setError("");
              }}
              required
            />
            {fieldErrors.password && <div className="field-error">{fieldErrors.password}</div>}
          </label>
          {error && <div className="auth-error">{error}</div>}
          <button className="button primary" type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create Account"}
          </button>
        </form>
        <div className="auth-footer">
          <span>Already have access?</span>
          <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
