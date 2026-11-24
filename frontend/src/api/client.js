import * as mock from "./mock";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

async function request(path, options = {}) {
  const isForm = options.body instanceof FormData;
  const res = await fetch(BASE + path, {
    headers: isForm ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`Server error (${res.status}). Backend chalu ache to?`);
  return res.json();
}

const json = (method, body) => ({ method, body: JSON.stringify(body) });

export const api = {
  // Daily digest: /alerts/today
  getAlertsToday: () => (USE_MOCK ? mock.getAlertsToday() : request("/alerts/today")),
  // body: { medicine_name, action: "DONE" | "SNOOZE" | "DISMISS", snooze_days? }
  sendAction: (p) => (USE_MOCK ? mock.sendAction(p) : request("/actions/", json("POST", p))),

  getMedicines: () => (USE_MOCK ? mock.getMedicines() : request("/medicines/")),
  addMedicine: (m) => (USE_MOCK ? mock.addMedicine(m) : request("/medicines/", json("POST", m))),
  deleteMedicine: (id) =>
    USE_MOCK ? mock.deleteMedicine(id) : request(`/medicines/${id}`, { method: "DELETE" }),
  importMedicines: (file, rows) => {
    if (USE_MOCK) return mock.importMedicines(rows);
    const fd = new FormData();
    fd.append("file", file);
    return request("/medicines/import", { method: "POST", body: fd });
  },

  getCompanies: () => (USE_MOCK ? mock.getCompanies() : request("/companies/")),
  saveCompany: (c) =>
    USE_MOCK
      ? mock.saveCompany(c)
      : c.id
      ? request(`/companies/${c.id}`, json("PUT", c))
      : request("/companies/", json("POST", c)),
  deleteCompany: (id) =>
    USE_MOCK ? mock.deleteCompany(id) : request(`/companies/${id}`, { method: "DELETE" }),
};
