import React from "react";
import ReactDOM from "react-dom/client";

import SimpleApp from "./SimpleApp";
import "./styles.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Root element not found");
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <SimpleApp />
  </React.StrictMode>
);
