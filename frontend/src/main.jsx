import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Toaster } from "react-hot-toast";

import App from "./App.jsx";
import "./styles/globals.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        style: { fontSize: "13px" },
        duration: 3000,
      }}
    />
  </StrictMode>
);
