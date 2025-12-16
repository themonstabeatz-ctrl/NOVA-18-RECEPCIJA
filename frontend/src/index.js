import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// 🔐 HARD FAIL GUARD - Ensure correct backend URL
if (!process.env.REACT_APP_BACKEND_URL?.includes("massage-scheduler-4")) {
  throw new Error("FATAL: Invalid backend URL. Check REACT_APP_BACKEND_URL.");
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
