import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      await register({ ...form, username: form.name });
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-art">
        <div className="auth-brand">AI Wardrobe</div>
        <div className="auth-quote">
          Your closet,
          <br />
          <em>your signature.</em>
        </div>
        <div className="auth-art-card">A calmer way to get dressed.</div>
      </div>

      <div className="auth-panel">
        <div className="auth-box">
          <div className="eyebrow">CREATE YOUR STUDIO</div>
          <h1>Make it yours.</h1>
          <p className="auth-subtitle">
            Start with the clothes you already love.
          </p>

          {error && <div className="error-box">{error}</div>}

          <form onSubmit={handleSubmit} className="form">
            <label>
              Name
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                required
                placeholder="Your name"
              />
            </label>

            <label>
              Email
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
                placeholder="you@example.com"
              />
            </label>

            <label>
              Password
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                required
                placeholder="Your password"
              />
            </label>

            <button
              className="button button-primary full"
              disabled={busy}
              type="submit"
            >
              {busy ? "Creating…" : "Create account"}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
