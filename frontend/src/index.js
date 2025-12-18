import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// 🔐 Backend URL validation (spa-booking-api is the correct backend)
const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
console.log('🔧 Backend URL:', backendUrl);

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
