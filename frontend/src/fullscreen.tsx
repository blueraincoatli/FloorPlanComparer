import React from "react";
import ReactDOM from "react-dom/client";

import { FullScreenView } from "./pages/FullScreenView";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <FullScreenView />
  </React.StrictMode>
);
