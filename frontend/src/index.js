import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// 🔐 HARD-LOCKED URLs - ONLY THESE ARE VALID
const BACKEND_PUBLIC_URL = "https://spa-integration.preview.emergentagent.com";
const FRONTEND_PUBLIC_URL = "https://relax-reserve-5.preview.emergentagent.com";

const backendUrl = process.env.REACT_APP_BACKEND_URL || BACKEND_PUBLIC_URL;
console.log('🔐 LOCKED BACKEND_PUBLIC_URL =', BACKEND_PUBLIC_URL);
console.log('🔐 LOCKED FRONTEND_PUBLIC_URL =', FRONTEND_PUBLIC_URL);
console.log('🔧 Active Backend URL:', backendUrl);

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
