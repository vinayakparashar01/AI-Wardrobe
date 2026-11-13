import React, { createContext, useCallback, useContext, useState } from "react";
import { AlertCircle, Check, Info, X } from "lucide-react";

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = "success", duration = 3500) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div
        className="toast-container"
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          zIndex: 9999,
          pointerEvents: "none",
        }}
        aria-live="polite"
      >
        {toasts.map((toast) => {
          const isError = toast.type === "error";
          const isInfo = toast.type === "info";

          let bgColor = "#1f1d1d";
          let IconComponent = Check;
          let iconColor = "#4ade80";

          if (isError) {
            bgColor = "#450a0a";
            IconComponent = AlertCircle;
            iconColor = "#f87171";
          } else if (isInfo) {
            bgColor = "#0f172a";
            IconComponent = Info;
            iconColor = "#38bdf8";
          }

          return (
            <div
              key={toast.id}
              style={{
                pointerEvents: "auto",
                background: bgColor,
                color: "#ffffff",
                padding: "12px 18px",
                borderRadius: "12px",
                boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                fontSize: "14px",
                fontWeight: "500",
                minWidth: "260px",
                maxWidth: "400px",
                border: isError
                  ? "1px solid #7f1d1d"
                  : isInfo
                  ? "1px solid #1e293b"
                  : "1px solid #332d2d",
              }}
            >
              <IconComponent size={18} color={iconColor} style={{ flexShrink: 0 }} />
              <span style={{ flex: 1, lineHeight: "1.3" }}>{toast.message}</span>
              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                style={{
                  background: "transparent",
                  border: 0,
                  color: "rgba(255,255,255,0.6)",
                  cursor: "pointer",
                  padding: "2px",
                  display: "grid",
                  placeItems: "center",
                  flexShrink: 0,
                }}
                aria-label="Dismiss notification"
              >
                <X size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    return {
      showToast: (msg) => console.log("Toast notification:", msg),
    };
  }
  return ctx;
};
