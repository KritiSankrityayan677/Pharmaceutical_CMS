import React from "react";
import ComplaintForm from "./components/ComplaintForm";
import ChatCopilot from "./components/ChatCopilot";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-dot" />
          <div>
            <div className="brand-name">AIVOA</div>
            <div className="brand-sub">Customer Complaint Management</div>
          </div>
        </div>
        <span className="pill">QMS · Complaints Module</span>
      </header>

      <main className="main-grid">
        <section className="col form-col">
          <ComplaintForm />
        </section>
        <aside className="col chat-col">
          <ChatCopilot />
        </aside>
      </main>
    </div>
  );
}
