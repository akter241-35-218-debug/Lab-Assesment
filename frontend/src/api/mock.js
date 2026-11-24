// Sample data: backend ready na thakle ei data diye UI cholbe.
const wait = (v, ms = 250) =>
  new Promise((r) => setTimeout(() => r(JSON.parse(JSON.stringify(v))), ms));

let companies = [
  { id: 1, name: "ACI", return_window_days: 90, discount_allowed: true, max_discount_pct: 20 },
  { id: 2, name: "Square", return_window_days: 60, discount_allowed: true, max_discount_pct: 15 },
  { id: 3, name: "Beximco", return_window_days: 0, discount_allowed: false, max_discount_pct: 0 },
];

let medicines = [
  { id: 1, name: "Napa Extra", quantity: 40, expiry_date: "2027-03-31", company: "ACI", cost_price: 20 },
  { id: 2, name: "Seclo 20mg", quantity: 12, expiry_date: "2027-01-31", company: "Square", cost_price: 60 },
  { id: 3, name: "Cough Syrup 100ml", quantity: 6, expiry_date: "2026-12-31", company: "Beximco", cost_price: 85 },
  { id: 4, name: "Ace Plus", quantity: 30, expiry_date: "2027-02-28", company: "Square", cost_price: 12 },
  { id: 5, name: "Zimax 500mg", quantity: 20, expiry_date: "2027-06-30", company: "ACI", cost_price: 95 },
];

let alerts = [
  { name: "Seclo 20mg", company: "Square", quantity: 12, risk: "HIGH", action: "RETURN",
    reason: "Return deadline in 8 days; stock will take about 120 days to sell",
    priority: 82.4, potential_loss: 720, days_to_expiry: 68, days_to_return_deadline: 8 },
  { name: "Zimax 500mg", company: "ACI", quantity: 20, risk: "HIGH", action: "RETURN",
    reason: "Return deadline in 12 days; sells only 1 strip per week",
    priority: 71.0, potential_loss: 1900, days_to_expiry: 218, days_to_return_deadline: 12 },
  { name: "Ace Plus", company: "Square", quantity: 30, risk: "MEDIUM", action: "DISCOUNT",
    reason: "Return window closed; discount up to 15% to sell before expiry",
    priority: 58.3, potential_loss: 360, days_to_expiry: 96, days_to_return_deadline: -3 },
  { name: "Cough Syrup 100ml", company: "Beximco", quantity: 6, risk: "MEDIUM", action: "OTHER",
    reason: "No return and no discount allowed: transfer, bundle offer or plan write-off",
    priority: 55.9, potential_loss: 510, days_to_expiry: 37, days_to_return_deadline: null },
];

export const getAlertsToday = () =>
  wait([...alerts].sort((a, b) => b.priority - a.priority));

export const sendAction = ({ medicine_name }) => {
  alerts = alerts.filter((a) => a.name !== medicine_name);
  return wait({ ok: true }, 150);
};

export const getMedicines = () => wait(medicines);
export const addMedicine = (m) => {
  medicines = [...medicines, { ...m, id: Date.now() }];
  return wait({ ok: true });
};
export const deleteMedicine = (id) => {
  medicines = medicines.filter((m) => m.id !== id);
  return wait({ ok: true }, 150);
};
export const importMedicines = (rows) => {
  const added = rows.map((r, i) => ({
    id: Date.now() + i,
    name: r.name,
    quantity: Number(r.quantity) || 0,
    expiry_date: r.expiry_date,
    company: r.company,
    cost_price: Number(r.cost_price) || 0,
  }));
  medicines = [...medicines, ...added];
  return wait({ imported: added.length });
};

export const getCompanies = () => wait(companies);
export const saveCompany = (c) => {
  if (c.id) companies = companies.map((x) => (x.id === c.id ? c : x));
  else companies = [...companies, { ...c, id: Date.now() }];
  return wait({ ok: true });
};
export const deleteCompany = (id) => {
  companies = companies.filter((c) => c.id !== id);
  return wait({ ok: true }, 150);
};
