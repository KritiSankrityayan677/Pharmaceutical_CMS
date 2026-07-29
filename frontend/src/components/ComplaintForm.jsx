import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { updateFormField, saveComplaintThunk, resetAll } from "../store/complaintSlice";
import RiskAssessmentBox from "./RiskAssessmentBox";

/**
 * The Log Customer Complaint form.
 *
 * Structure matches the reference UI:
 *   1. Origin & Customer Details
 *   2. Product & Batch Identification
 *   3. Complaint Details
 *   4. Defect Analysis   (Complaint Category + embedded AI Copilot Risk Assessment)
 *   5. Initial Assessment & Priority
 *
 * Every field is controlled by Redux and shows the "Awaiting AI extraction..."
 * placeholder before the user prompts the copilot.
 */

const COMPLAINT_SOURCES = [
  "", "Email", "Phone", "Portal", "Distributor Report", "Regulator", "Other",
];
const COMPLAINT_TYPES = [
  "", "Product Quality", "Adverse Event", "Packaging", "Labeling", "Efficacy", "Other",
];
const SEVERITIES = ["", "Critical", "Major", "Minor"];
const PRIORITIES = ["", "P1 - Urgent", "P2 - High", "P3 - Normal", "P4 - Low"];

const PLACEHOLDER = "Awaiting AI extraction...";

function Field({ label, children }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
    </label>
  );
}

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const form = useSelector((s) => s.complaint.form);
  const risk = useSelector((s) => s.complaint.riskAssessment);
  const saved = useSelector((s) => s.complaint.savedComplaintNumber);
  const status = useSelector((s) => s.complaint.status);

  const set = (key) => (e) =>
    dispatch(updateFormField({ key, value: e.target.value }));

  const onSave = () => {
    if (!form.product_name && !form.detailed_complaint_description) {
      alert("Ask the AI Copilot to extract the complaint details first.");
      return;
    }
    dispatch(saveComplaintThunk());
  };

  return (
    <div className="form-card">
      <div className="form-header">
        <div>
          <h1 className="form-title">Log Customer Complaint</h1>
          <div className="form-subtitle">API &amp; FDF Quality Assurance Module</div>
        </div>
        <span className="triage-pill">Pending Triage</span>
      </div>

      {/* SECTION 1 -------------------------------------------------------- */}
      <div className="form-section">
        <h3><span className="sec-num">1.</span> Origin &amp; Customer Details</h3>
        <div className="form-grid two">
          <Field label="Complaint Source">
            <select value={form.complaint_source || ""} onChange={set("complaint_source")}>
              {COMPLAINT_SOURCES.map((v) => (
                <option key={v} value={v}>{v || PLACEHOLDER}</option>
              ))}
            </select>
          </Field>
          <Field label="Customer Name">
            <input
              placeholder={PLACEHOLDER}
              value={form.customer_name || ""}
              onChange={set("customer_name")}
            />
          </Field>
        </div>
      </div>

      {/* SECTION 2 -------------------------------------------------------- */}
      <div className="form-section">
        <h3><span className="sec-num">2.</span> Product &amp; Batch Identification</h3>
        <div className="form-grid two">
          <Field label="Product Name">
            <input placeholder={PLACEHOLDER} value={form.product_name || ""} onChange={set("product_name")} />
          </Field>
          <Field label="Product Strength / Grade">
            <input placeholder={PLACEHOLDER} value={form.product_strength_grade || ""} onChange={set("product_strength_grade")} />
          </Field>
          <Field label="Batch / Lot Number">
            <input placeholder={PLACEHOLDER} value={form.batch_number || ""} onChange={set("batch_number")} />
          </Field>
          <Field label="Manufacturing Date">
            <input placeholder={PLACEHOLDER} value={form.manufacturing_date || ""} onChange={set("manufacturing_date")} />
          </Field>
          <Field label="Expiry Date">
            <input placeholder={PLACEHOLDER} value={form.expiry_date || ""} onChange={set("expiry_date")} />
          </Field>
          <Field label="Quantity Affected">
            <input placeholder={PLACEHOLDER} value={form.quantity_affected || ""} onChange={set("quantity_affected")} />
          </Field>
        </div>
      </div>

      {/* SECTION 3 -------------------------------------------------------- */}
      <div className="form-section">
        <h3><span className="sec-num">3.</span> Complaint Details</h3>
        <div className="form-grid two">
          <Field label="Complaint Type">
            <select value={form.complaint_type || ""} onChange={set("complaint_type")}>
              {COMPLAINT_TYPES.map((v) => (
                <option key={v} value={v}>{v || PLACEHOLDER}</option>
              ))}
            </select>
          </Field>
          <Field label="Complaint Date">
            <input placeholder={PLACEHOLDER} value={form.complaint_date || ""} onChange={set("complaint_date")} />
          </Field>
        </div>
        <Field label="Detailed Complaint Description">
          <textarea
            rows={4}
            placeholder={PLACEHOLDER}
            value={form.detailed_complaint_description || ""}
            onChange={set("detailed_complaint_description")}
          />
        </Field>
      </div>

      {/* SECTION 4 - Defect Analysis + embedded AI Copilot Risk Assessment */}
      <div className="form-section">
        <h3><span className="sec-num">4.</span> Defect Analysis</h3>
        <Field label="Complaint Category">
          <input
            placeholder={PLACEHOLDER}
            value={form.complaint_category || ""}
            onChange={set("complaint_category")}
          />
        </Field>
        <RiskAssessmentBox risk={risk} />
      </div>

      {/* SECTION 5 -------------------------------------------------------- */}
      <div className="form-section">
        <h3><span className="sec-num">5.</span> Initial Assessment &amp; Priority</h3>
        <div className="form-grid two">
          <Field label="Initial Severity">
            <select value={form.initial_severity || ""} onChange={set("initial_severity")}>
              {SEVERITIES.map((v) => (
                <option key={v} value={v}>{v || PLACEHOLDER}</option>
              ))}
            </select>
          </Field>
          <Field label="Priority">
            <select value={form.priority || ""} onChange={set("priority")}>
              {PRIORITIES.map((v) => (
                <option key={v} value={v}>{v || PLACEHOLDER}</option>
              ))}
            </select>
          </Field>
        </div>
      </div>

      {/* FOOTER ----------------------------------------------------------- */}
      <div className="form-footer">
        <button className="btn btn-ghost" onClick={() => dispatch(resetAll())} disabled={status === "loading"}>
          ↺ Reset Form
        </button>
        <button className="btn btn-primary btn-commit" onClick={onSave} disabled={status === "loading"}>
          📥 Commit to QMS Ledger
        </button>
        {saved && <span className="saved-pill">Saved as {saved}</span>}
      </div>
    </div>
  );
}
