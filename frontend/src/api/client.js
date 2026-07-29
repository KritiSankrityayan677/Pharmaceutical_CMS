import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const api = axios.create({ baseURL: BASE_URL, timeout: 180_000 });

/**
 * Unified chat call. Sends the user's message + current form state + history,
 * plus optional file. Backend routes to extract / update / question internally.
 */
export async function sendChat({ message, file, currentForm, history }) {
  const fd = new FormData();
  fd.append("message", message || "");
  fd.append("current_form", JSON.stringify(currentForm || {}));
  fd.append("history", JSON.stringify(history || []));
  if (file) fd.append("file", file);
  const { data } = await api.post("/ai/chat", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function saveComplaint(payload) {
  const { data } = await api.post("/complaints/save", payload);
  return data;
}

export async function listComplaints() {
  const { data } = await api.get("/complaints/");
  return data;
}

export default api;
