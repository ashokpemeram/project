import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login as loginRequest } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { validateEmail } from "../utils/validation";
import "./Auth.css";

export default function AdminLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { token, user, login } = useAuth();

  useEffect(() => {
    if (token && user?.role === "admin") {
      navigate("/admin", { replace: true });
    }
  }, [token, user, navigate]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    const nextErrors = {};
    const emailError = validateEmail(email);
    if (emailError) nextErrors.email = emailError;
    if (!String(password ?? "").trim()) nextErrors.password = "Password is required.";
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      return;
    }

    setLoading(true);
    try {
      const data = await loginRequest({ email: email.trim(), password });
      if (data.user?.role !== "admin") {
        setError("This account is not an admin.");
        return;
      }
      login({ token: data.token, user: data.user });
      navigate("/admin");
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card card fade-up">
        <div className="auth-header">
          <h1>Admin Sign In</h1>
          <p>Manage doctors and patient records.</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
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
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <div className="auth-footer">
          <span>Doctor access?</span>
          <Link to="/login">Doctor login</Link>
        </div>
      </div>
    </div>
  );
}

