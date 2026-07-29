import React from "react";

/**
 * The blue "AI Copilot Risk Assessment" box shown inside Section 4 of the form
 * (matches the reference screenshot).
 *
 * It's populated from state.complaint.riskAssessment, which the LangGraph
 * `risk_assessment` node produces during the extract path. Shows a friendly
 * empty state until the AI has run.
 */
export default function RiskAssessmentBox({ risk }) {
  if (!risk) {
    return (
      <div className="risk-box risk-empty">
        <div className="risk-box-header">
          <span className="shield">🛡</span>
          <span>AI Copilot Risk Assessment</span>
        </div>
        <div className="risk-empty-body">
          Awaiting complaint details. Once you upload a document or describe the
          complaint in the chat, I'll suggest severity, next action and initial
          risk assessment here.
        </div>
      </div>
    );
  }

  return (
    <div className="risk-box">
      <div className="risk-box-header">
        <span className="shield">🛡</span>
        <span>AI Copilot Risk Assessment</span>
        {risk.risk_level && (
          <span className={`risk-badge risk-badge-${risk.risk_level.toLowerCase()}`}>
            {risk.risk_level}
          </span>
        )}
      </div>

      <div className="risk-grid">
        <div className="risk-field">
          <div className="risk-label">Severity (Suggested)</div>
          <div className={`risk-value sev sev-${(risk.severity_suggested || "").toLowerCase()}`}>
            {risk.severity_suggested || "—"}
          </div>
        </div>
        <div className="risk-field">
          <div className="risk-label">Suggested Next Action</div>
          <div className="risk-value">{risk.suggested_next_action || "—"}</div>
        </div>
      </div>

      <div className="risk-field">
        <div className="risk-label">Initial Risk Assessment</div>
        <div className="risk-value risk-para">{risk.initial_risk_assessment || "—"}</div>
      </div>

      {(risk.patient_safety_impact || risk.regulatory_impact) && (
        <details className="risk-details">
          <summary>More detail (patient safety &amp; regulatory)</summary>
          {risk.patient_safety_impact && (
            <p><b>Patient safety:</b> {risk.patient_safety_impact}</p>
          )}
          {risk.regulatory_impact && (
            <p><b>Regulatory:</b> {risk.regulatory_impact}</p>
          )}
        </details>
      )}
    </div>
  );
}
