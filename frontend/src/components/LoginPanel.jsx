import React, { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function LoginPanel({ onRegisterSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [username, setUsername] = useState(""); // for login (can be email)
  const [password, setPassword] = useState("");

  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regPassword2, setRegPassword2] = useState("");

  const [captchaA, setCaptchaA] = useState(0);
  const [captchaB, setCaptchaB] = useState(0);
  const [captchaAnswer, setCaptchaAnswer] = useState("");

  const [message, setMessage] = useState("");

  const token = localStorage.getItem("access_token");

  function generateCaptcha() {
    const a = Math.floor(Math.random() * 9) + 1; // 1..9
    const b = Math.floor(Math.random() * 9) + 1;
    setCaptchaA(a);
    setCaptchaB(b);
    setCaptchaAnswer("");
  }

  useEffect(() => {
    if (mode === "register") {
      generateCaptcha();
    }
  }, [mode]);

  async function handleLogin(e) {
    e.preventDefault();
    setMessage("");

    try {
      const body = new URLSearchParams();
      body.append("username", username);
      body.append("password", password);

      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
      });

      if (!res.ok) {
        const txt = await res.text();
        console.error(txt);
        setMessage("Login failed. Check username/password or activation status.");
        return;
      }

      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      setMessage("Login successful. Reloading...");
      setTimeout(() => window.location.reload(), 700);
    } catch (err) {
      console.error(err);
      setMessage("Error during login.");
    }
  }

    async function handleRegister(e) {
      e.preventDefault();
      setMessage("");
    
      // ...validaciones locales...
    
      try {
        const res = await fetch(`${API_BASE}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: regEmail,
            password: regPassword,
            captcha_a: captchaA,
            captcha_b: captchaB,
            captcha_result: Number(captchaAnswer),
          }),
        });
    
        if (!res.ok) {
          const text = await res.text();
          console.error("register error", res.status, text);
    
          let msg = "Registration failed.";
          try {
            const data = JSON.parse(text);
            if (Array.isArray(data.detail) && data.detail.length > 0) {
              msg = data.detail[0].msg;
            } else if (typeof data.detail === "string") {
              msg = data.detail;
            }
          } catch (_) {}
    
          setMessage(msg);
          generateCaptcha();
          return;
        }
    
        // 🎯 ÉXITO:
        alert("User Created Successfully");
    
        // si quieres limpiar el formulario:
        setRegEmail("");
        setRegPassword("");
        setRegPassword2("");
        generateCaptcha();
        setMessage("");
    
        // avisamos al padre que el registro salió bien
        if (onRegisterSuccess) {
          onRegisterSuccess();
        }
    
      } catch (err) {
        console.error(err);
        setMessage("Error during registration.");
      }
    }

  function handleLogout() {
    localStorage.removeItem("access_token");
    setMessage("Logged out. Reloading...");
    setTimeout(() => window.location.reload(), 500);
  }

  if (token) {
    return (
      <div className="flex items-center gap-3 text-xs text-slate-300">
        <span>Session active</span>
        <button
          onClick={handleLogout}
          className="rounded-md border border-slate-600 px-2 py-1 hover:bg-slate-800"
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-1 text-xs">
      <div className="flex items-center gap-2 mb-1">
        <button
          className={
            mode === "login"
              ? "font-semibold text-slate-100 underline"
              : "text-slate-400"
          }
          onClick={() => setMode("login")}
          type="button"
        >
          Login
        </button>
        <button
          className={
            mode === "register"
              ? "font-semibold text-slate-100 underline"
              : "text-slate-400"
          }
          onClick={() => setMode("register")}
          type="button"
        >
          Create account
        </button>
      </div>

      {mode === "login" ? (
        <form onSubmit={handleLogin} className="flex items-center gap-2">
          <input
            type="text"
            placeholder="email or username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="rounded-md bg-slate-900 border border-slate-700 px-2 py-1"
          />
          <input
            type="password"
            placeholder="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md bg-slate-900 border border-slate-700 px-2 py-1"
          />
          <button
            type="submit"
            className="rounded-md bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3 py-1 font-medium"
          >
            Login
          </button>
        </form>
      ) : (
        <form onSubmit={handleRegister} className="flex flex-col gap-1 items-end">
          <div className="flex gap-2">
            <input
              type="email"
              placeholder="email"
              value={regEmail}
              onChange={(e) => setRegEmail(e.target.value)}
              className="rounded-md bg-slate-900 border border-slate-700 px-2 py-1"
            />
            <input
              type="password"
              placeholder="password"
              value={regPassword}
              onChange={(e) => setRegPassword(e.target.value)}
              className="rounded-md bg-slate-900 border border-slate-700 px-2 py-1"
            />
            <input
              type="password"
              placeholder="confirm"
              value={regPassword2}
              onChange={(e) => setRegPassword2(e.target.value)}
              className="rounded-md bg-slate-900 border border-slate-700 px-2 py-1"
            />
          </div>
          <div className="flex items-center gap-2">
            <span>
              Captcha: {captchaA} + {captchaB} =
            </span>
            <input
              type="number"
              value={captchaAnswer}
              onChange={(e) => setCaptchaAnswer(e.target.value)}
              className="w-16 rounded-md bg-slate-900 border border-slate-700 px-2 py-1"
            />
            <button
              type="button"
              onClick={generateCaptcha}
              className="rounded-md border border-slate-600 px-2 py-1 hover:bg-slate-800"
            >
              ↻
            </button>
            <button
              type="submit"
              className="rounded-md bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3 py-1 font-medium"
            >
              Register
            </button>
          </div>
        </form>
      )}

      {message && <span className="text-slate-400">{message}</span>}
    </div>
  );
}

export default LoginPanel;
