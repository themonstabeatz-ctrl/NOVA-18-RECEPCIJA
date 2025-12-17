import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// 🔐 HARD FAIL GUARD - Ensure correct backend URL
if (!process.env.REACT_APP_BACKEND_URL?.includes("spa-dashboard-2")) {
  throw new Error("FATAL: Invalid backend URL. Check REACT_APP_BACKEND_URL.");
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
