import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChat, saveComplaint } from "../api/client";

// Empty form aligned with backend ComplaintForm schema (5 sections).
const emptyForm = {
  // 1. Origin & Customer
  complaint_source: "",
  customer_name: "",
  // 2. Product & Batch
  product_name: "",
  product_strength_grade: "",
  batch_number: "",
  manufacturing_date: "",
  expiry_date: "",
  quantity_affected: "",
  // 3. Complaint Details
  complaint_type: "",
  complaint_date: "",
  detailed_complaint_description: "",
  // 4. Defect Analysis
  complaint_category: "",
  // 5. Initial Assessment & Priority
  initial_severity: "",
  priority: "",
};

const initialState = {
  form: { ...emptyForm },
  // AI copilot outputs (persist across chat turns; overwritten on new extraction)
  riskAssessment: null,
  completeness: null,
  rootCauseHypotheses: [],
  capaRecommendation: null,
  summary: null,
  duplicateOfNumber: null,

  // Chat
  history: [
    {
      role: "assistant",
      content:
        "Upload a complaint document or paste text above. I'll automatically extract the details and populate the form for you.",
    },
  ],
  status: "idle",         // idle | loading | succeeded | failed
  extractionProgress: 0,  // 0-100
  lastIntent: null,       // extract | update | question - for the trace label

  savedComplaintNumber: null,
  error: null,
};

// --- Thunks ---

export const sendChatThunk = createAsyncThunk(
  "complaint/sendChat",
  async ({ message, file }, { getState }) => {
    const { form, history } = getState().complaint;
    return await sendChat({ message, file, currentForm: form, history });
  },
);

export const saveComplaintThunk = createAsyncThunk(
  "complaint/save",
  async (_, { getState }) => {
    const s = getState().complaint;
    return await saveComplaint({
      form: s.form,
      risk_assessment: s.riskAssessment,
      completeness: s.completeness,
      root_cause_hypotheses: s.rootCauseHypotheses,
      capa_recommendation: s.capaRecommendation,
      summary: s.summary,
      duplicate_of_complaint_number: s.duplicateOfNumber,
      source_type: "chat",
      raw_input: "",
      conversation: s.history,
    });
  },
);

const slice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    // Manual edits from the form UI.
    updateFormField(state, action) {
      const { key, value } = action.payload;
      state.form[key] = value;
    },
    // Optimistic user message + optional file mention added to the chat before the API returns.
    appendUserMessage(state, action) {
      const { text, fileName } = action.payload;
      const content = fileName ? `${text || ""}\n[Attached: ${fileName}]`.trim() : text;
      state.history.push({ role: "user", content });
    },
    resetAll() {
      return { ...initialState, history: [...initialState.history] };
    },
    // Fake progress bar tick during extraction (nice UX, cheap to implement).
    setProgress(state, action) {
      state.extractionProgress = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatThunk.pending, (state) => {
        state.status = "loading";
        state.error = null;
        state.extractionProgress = 10;
      })
      .addCase(sendChatThunk.fulfilled, (state, action) => {
        const r = action.payload;
        state.status = "succeeded";
        state.extractionProgress = 100;
        state.lastIntent = r.intent;

        // Merge form patch (only keys the AI actually returned).
        Object.entries(r.form_patch || {}).forEach(([k, v]) => {
          if (v !== null && v !== undefined && k in state.form) {
            state.form[k] = v;
          }
        });

        // If the AI produced a risk assessment this turn, adopt it.
        // Also mirror severity_suggested into initial_severity if user hasn't set it.
        if (r.risk_assessment) {
          state.riskAssessment = r.risk_assessment;
          if (!state.form.initial_severity && r.risk_assessment.severity_suggested) {
            state.form.initial_severity = r.risk_assessment.severity_suggested;
          }
        }
        if (r.completeness) state.completeness = r.completeness;
        if (r.root_cause_hypotheses?.length) state.rootCauseHypotheses = r.root_cause_hypotheses;
        if (r.capa_recommendation) state.capaRecommendation = r.capa_recommendation;
        if (r.summary) state.summary = r.summary;
        if (r.duplicate_of_complaint_number !== undefined) {
          state.duplicateOfNumber = r.duplicate_of_complaint_number;
        }

        state.history.push({ role: "assistant", content: r.assistant_message });
      })
      .addCase(sendChatThunk.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error?.message || "Something went wrong";
        state.extractionProgress = 0;
        state.history.push({
          role: "assistant",
          content: "Sorry - I hit an error processing that. Please try again.",
        });
      })
      .addCase(saveComplaintThunk.fulfilled, (state, action) => {
        state.savedComplaintNumber = action.payload.complaint_number;
      });
  },
});

export const { updateFormField, appendUserMessage, resetAll, setProgress } = slice.actions;
export default slice.reducer;
