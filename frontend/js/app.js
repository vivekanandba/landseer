// Landseer SPA: hash router + views over the typed backend API.
import { api, ApiError, getBase, setBase, getToken, setToken } from "./api.js";
import {
  h,
  clear,
  inr,
  sqft,
  titlecase,
  statusBadge,
  docBadge,
  meter,
  spinner,
  empty,
  errorBanner,
  tile,
  dataTable,
  formModal,
  csv,
  parseVertices,
  escapeHtml,
} from "./ui.js";

const STATUSES = ["evaluating", "shortlisted", "rejected", "purchased"];
const DOC_TYPES = ["patta", "fmb", "ec", "deed", "land_record", "notes", "photo", "document", "unknown"];
const DIRECTIONS = ["", "north", "south", "east", "west"];

const viewEl = document.getElementById("view");
const crumbEl = document.getElementById("crumb");
const connEl = document.getElementById("conn");
const DEFAULT_PREF = "My Ideal Plot";

// ---- Router ----
const routes = [
  { re: /^\/$/, title: "Dashboard", view: dashboardView },
  { re: /^\/properties$/, title: "Properties", view: propertiesView },
  { re: /^\/properties\/(\d+)$/, title: "Property", view: propertyDetailView },
  { re: /^\/recommendations$/, title: "Recommendations", view: recommendationsView },
  { re: /^\/compare$/, title: "Compare", view: compareView },
  { re: /^\/brokers$/, title: "Brokers", view: brokersView },
];

let renderSeq = 0;

async function render() {
  const token = ++renderSeq;
  const isStale = () => token !== renderSeq;

  // Route on the path only; the query string (?foo=bar) is read separately.
  const path = (location.hash || "#/").slice(1).split("?")[0];
  const match = routes.map((r) => ({ r, m: path.match(r.re) })).find((x) => x.m);
  const { r, m } = match || { r: routes[0], m: ["/"] };

  const top = path === "/" ? "/" : "/" + path.split("/")[1];
  document.querySelectorAll("#nav a").forEach((a) => {
    a.classList.toggle("active", a.dataset.route === top);
  });
  crumbEl.textContent = r.title;

  clear(viewEl).appendChild(spinner());
  try {
    const node = await r.view(...m.slice(1));
    if (isStale()) return; // a newer navigation superseded this one
    clear(viewEl).appendChild(node);
  } catch (e) {
    if (isStale()) return;
    const msg = e instanceof ApiError ? `${e.message}` : `Unexpected error: ${e.message}`;
    clear(viewEl).appendChild(errorBanner(msg));
    if (e instanceof ApiError && e.status === 401) {
      viewEl.appendChild(empty("This API requires a token — open Settings to set one."));
    }
  }
}

window.addEventListener("hashchange", render);

// ---- Views ----
function pageHead(title, sub) {
  return h("div", null, [h("h1.page-title", null, title), sub ? h("p.page-sub", null, sub) : null]);
}

async function dashboardView() {
  const [props, notes] = await Promise.all([
    api.properties({ limit: 500 }),
    api.notifications().catch(() => ({ expiring_documents: [], price_alerts: [], follow_ups: [] })),
  ]);

  const byStatus = { evaluating: 0, shortlisted: 0, purchased: 0, rejected: 0 };
  let totalValue = 0;
  for (const p of props) {
    byStatus[p.status] = (byStatus[p.status] || 0) + 1;
    if (p.status !== "rejected") totalValue += p.asking_price || 0;
  }
  const noteCount =
    notes.expiring_documents.length + notes.price_alerts.length + notes.follow_ups.length;

  const wrap = h("div", null, [pageHead("Dashboard", "Portfolio at a glance")]);

  wrap.appendChild(
    h("div.grid.tiles", null, [
      tile("Properties tracked", String(props.length), `${byStatus.shortlisted} shortlisted`),
      tile("Pipeline value", inr(totalValue), "excludes rejected"),
      tile("Evaluating", String(byStatus.evaluating || 0), "under active review"),
      tile("Alerts", String(noteCount), "needs attention", false),
    ]),
  );

  wrap.appendChild(h("h2.section-title", null, "Needs attention"));
  const noteCard = h("div.card.card-pad", null);
  if (!noteCount) noteCard.appendChild(empty("All clear — no expiries, price moves, or stale follow-ups."));
  for (const a of notes.price_alerts) {
    noteCard.appendChild(note("info", "↕", a.message));
  }
  for (const d of notes.expiring_documents) {
    noteCard.appendChild(note("warning", "⏳", d.message));
  }
  for (const f of notes.follow_ups) {
    noteCard.appendChild(note("serious", "☎", f.message));
  }
  wrap.appendChild(noteCard);

  wrap.appendChild(h("h2.section-title", null, "Recently updated"));
  const recent = [...props]
    .sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""))
    .slice(0, 6);
  wrap.appendChild(
    recent.length
      ? dataTable(
          [
            { key: "name", label: "Property" },
            { key: "location", label: "Location" },
            { key: "asking_price", label: "Asking", num: true, render: (r) => inr(r.asking_price) },
            { key: "status", label: "Status", render: (r) => statusBadge(r.status) },
          ],
          recent,
          (r) => (location.hash = `#/properties/${r.id}`),
        )
      : empty("No properties yet."),
  );
  return wrap;
}

function note(kind, ico, text) {
  return h("div.note", null, [
    h("div", { class: `note-ico ni-${kind}` }, ico),
    h("div.note-body", { html: escapeHtml(text) }),
  ]);
}

async function propertiesView() {
  const params = readQuery();
  const props = await api.properties({
    limit: 200,
    location: params.location,
    min_price: params.min_price,
    max_price: params.max_price,
  });

  const wrap = h("div", null, [
    h("div.title-row", null, [
      pageHead("Properties", `${props.length} shown`),
      h("button.btn", { onclick: openNewProperty }, "+ New property"),
    ]),
  ]);

  const locInput = h("input", { type: "text", placeholder: "e.g. Thuthikadu", value: params.location || "" });
  const minInput = h("input", { type: "number", placeholder: "min ₹", value: params.min_price || "" });
  const maxInput = h("input", { type: "number", placeholder: "max ₹", value: params.max_price || "" });
  const apply = () => {
    const q = new URLSearchParams();
    if (locInput.value) q.set("location", locInput.value);
    if (minInput.value) q.set("min_price", minInput.value);
    if (maxInput.value) q.set("max_price", maxInput.value);
    location.hash = "#/properties" + (q.toString() ? "?" + q.toString() : "");
  };
  wrap.appendChild(
    h("div.controls", null, [
      field("Location", locInput),
      field("Min price", minInput),
      field("Max price", maxInput),
      h("button.btn", { onclick: apply }, "Filter"),
      h("button.ghost-btn", { onclick: () => (location.hash = "#/properties") }, "Clear"),
    ]),
  );

  wrap.appendChild(
    props.length
      ? dataTable(
          [
            { key: "name", label: "Property" },
            { key: "survey_number", label: "Survey #" },
            { key: "location", label: "Location" },
            { key: "total_area_sqft", label: "Area", num: true, render: (r) => sqft(r.total_area_sqft) },
            { key: "asking_price", label: "Asking", num: true, render: (r) => inr(r.asking_price) },
            {
              key: "price_per_sqft",
              label: "₹/sqft",
              num: true,
              render: (r) => (r.price_per_sqft ? Math.round(r.price_per_sqft) : "—"),
            },
            { key: "status", label: "Status", render: (r) => statusBadge(r.status) },
          ],
          props,
          (r) => (location.hash = `#/properties/${r.id}`),
        )
      : empty("No properties match these filters."),
  );
  return wrap;
}

async function propertyDetailView(id) {
  const [p, docs, geo] = await Promise.all([
    api.property(id),
    api.documents(id).catch(() => []),
    api.mapGeojson(id).catch(() => null),
  ]);

  const wrap = h("div", null, [
    h("a.back-link", { href: "#/properties" }, "← Properties"),
    h("div", { style: "display:flex;align-items:center;gap:12px;flex-wrap:wrap" }, [
      h("h1.page-title", { style: "margin:0" }, p.name),
      statusBadge(p.status),
    ]),
    h("p.page-sub", null, [p.location, p.taluk, p.district].filter(Boolean).join(" · ")),
    h("div.toolbar", null, [
      h("button.btn", { onclick: () => openEditProperty(p) }, "Edit"),
      h("button.ghost-btn", { onclick: () => openAddSubdivision(p.id) }, "+ Subdivision"),
      h("button.ghost-btn", { onclick: () => openAddNeighbor(p.id) }, "+ Neighbor"),
      h("button.ghost-btn", { onclick: () => openUploadDocument(p.id) }, "+ Document"),
      h("button.ghost-btn", { onclick: () => openAddBoundary(p.id) }, "+ Boundary"),
    ]),
  ]);

  const facts = h("div.card.card-pad", null, [
    h("div.facts", null, [
      fact("Survey number", p.survey_number || "—"),
      fact("Total area", sqft(p.total_area_sqft)),
      fact("Asking price", inr(p.asking_price)),
      fact("Price / sqft", p.price_per_sqft ? `₹${Math.round(p.price_per_sqft)}` : "—"),
      fact("Water", featureText(p.water_source)),
      fact("Electricity", featureText(p.electricity)),
      fact("Road access", featureText(p.road_access)),
      fact("Corner plot", p.corner_plot ? "Yes" : "No"),
    ]),
    p.notes ? h("p", { style: "margin:16px 0 0;color:var(--text-secondary)" }, p.notes) : null,
  ]);

  const mapCard = h("div.card.card-pad", null, [
    h("div.tile-label", { style: "margin-bottom:10px" }, "Boundary"),
    geo && geo.features && geo.features.length ? boundarySvg(geo) : empty("No survey boundary yet."),
  ]);

  wrap.appendChild(h("div.detail-grid", null, [facts, mapCard]));

  // Subdivisions & neighbors
  const subN = h("div.grid.cols-2", { style: "margin-top:16px" }, [
    listCard(
      `Subdivisions (${(p.subdivisions || []).length})`,
      (p.subdivisions || []).map((s) => kv(s.name, sqft(s.area_sqft))),
      "No subdivisions.",
    ),
    listCard(
      `Neighbors (${(p.neighbors || []).length})`,
      (p.neighbors || []).map((n) =>
        kv(
          `${titlecase(n.direction || "—")} · ${n.survey_number}`,
          n.shared_boundary ? "shared boundary" : "",
        ),
      ),
      "No neighbors recorded.",
    ),
  ]);
  wrap.appendChild(subN);

  // Documents
  wrap.appendChild(h("h2.section-title", null, `Documents (${docs.length})`));
  wrap.appendChild(
    docs.length
      ? dataTable(
          [
            { key: "filename", label: "File" },
            { key: "doc_type", label: "Type", render: (r) => titlecase(r.doc_type) },
            { key: "status", label: "Status", render: (r) => docBadge(r.status) },
            {
              key: "extracted_survey_number",
              label: "OCR survey #",
              render: (r) => r.extracted_survey_number || "—",
            },
          ],
          docs,
        )
      : empty("No documents uploaded."),
  );
  return wrap;
}

async function recommendationsView() {
  const params = readQuery();
  const prefName = params.pref || DEFAULT_PREF;

  const wrap = h("div", null, [
    h("div.title-row", null, [
      pageHead("Recommendations", "Properties scored against your requirements"),
      h("button.btn", { onclick: openNewPreference }, "+ New preference"),
    ]),
  ]);

  const prefInput = h("input", { type: "text", value: prefName, style: "min-width:220px" });
  wrap.appendChild(
    h("div.controls", null, [
      field("Preference", prefInput),
      h(
        "button.btn",
        {
          onclick: () =>
            (location.hash = "#/recommendations?pref=" + encodeURIComponent(prefInput.value)),
        },
        "Load",
      ),
    ]),
  );

  let recs;
  try {
    recs = await api.recommendations(prefName);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      wrap.appendChild(empty(`No preference named “${prefName}”. Try another name.`));
      return wrap;
    }
    throw e;
  }

  if (!recs.length) return wrap.appendChild(empty("No properties to rank yet.")), wrap;

  wrap.appendChild(
    dataTable(
      [
        { key: "name", label: "Property" },
        { key: "score", label: "Match", render: (r) => meter(r.score) },
        {
          key: "disqualified",
          label: "Verdict",
          render: (r) =>
            r.disqualified
              ? h("span.badge.b-expired", null, "Deal-breaker")
              : h("span.badge.b-verified", null, "Eligible"),
        },
        {
          key: "reasons",
          label: "Notes",
          render: (r) =>
            h("span.muted", null, r.reasons && r.reasons.length ? r.reasons.join("; ") : "—"),
        },
      ],
      recs,
    ),
  );
  return wrap;
}

async function compareView() {
  const props = await api.properties({ limit: 200 });
  const wrap = h("div", null, [
    pageHead("Compare", "Build a side-by-side of shortlisted plots"),
  ]);

  if (props.length < 2) {
    wrap.appendChild(empty("Add at least two properties to compare."));
    return wrap;
  }

  const checks = new Map();
  const list = h(
    "div",
    { style: "display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px" },
    props.map((p) => {
      const cb = h("input", { type: "checkbox" });
      checks.set(p.id, cb);
      return h("label.chip", null, [cb, p.name]);
    }),
  );
  const nameInput = h("input", { type: "text", placeholder: "Comparison name", value: "Shortlist" });
  const result = h("div", { style: "margin-top:20px" });

  const runBtn = h(
    "button.btn",
    {
      onclick: async () => {
        const ids = [...checks.entries()].filter(([, cb]) => cb.checked).map(([id]) => id);
        if (ids.length < 2) {
          clear(result).appendChild(errorBanner("Pick at least two properties."));
          return;
        }
        const name = nameInput.value.trim() || "Shortlist";
        clear(result).appendChild(spinner("Building comparison…"));
        try {
          try {
            await api.createComparison(name, ids);
          } catch (e) {
            if (!(e instanceof ApiError && e.status === 409)) throw e; // 409 => reuse existing name
          }
          const [table, features, investment] = await Promise.all([
            api.comparisonTable(name),
            api.comparisonFeatures(name),
            api.comparisonInvestment(name),
          ]);
          clear(result);
          result.appendChild(renderComparison(table, features, investment));
        } catch (e) {
          clear(result).appendChild(errorBanner(e.message));
        }
      },
    },
    "Compare",
  );

  wrap.appendChild(
    h("div.card.card-pad", null, [
      h("div.tile-label", { style: "margin-bottom:10px" }, "Select properties"),
      list,
      h("div.controls", { style: "margin:0" }, [field("Name", nameInput), runBtn]),
    ]),
  );
  wrap.appendChild(result);

  // Deep link: #/compare?name=Foo renders that saved comparison directly.
  const preload = readQuery().name;
  if (preload) {
    nameInput.value = preload;
    try {
      const [table, features, investment] = await Promise.all([
        api.comparisonTable(preload),
        api.comparisonFeatures(preload),
        api.comparisonInvestment(preload),
      ]);
      result.appendChild(renderComparison(table, features, investment));
    } catch (e) {
      result.appendChild(errorBanner(e.message));
    }
  }
  return wrap;
}

function renderComparison(table, features, investment) {
  const box = h("div", null);

  // Table
  box.appendChild(h("h2.section-title", { style: "margin-top:0" }, "Overview"));
  const cols = [{ key: "name", label: "Property", render: (r) => r.name }].concat(
    table.columns.map((c) => ({
      key: c,
      label: c,
      num: c !== "Location" && c !== "Status",
      render: (r) => cellRender(c, r[c]),
    })),
  );
  box.appendChild(dataTable(cols, table.rows));

  // Features (colored dots)
  box.appendChild(h("h2.section-title", null, "Features"));
  const featNames = Object.keys(features);
  const featKeys = featNames.length ? Object.keys(features[featNames[0]]) : [];
  box.appendChild(
    dataTable(
      [{ key: "feat", label: "Feature", render: (r) => titlecase(r.feat) }].concat(
        featNames.map((pn) => ({
          key: pn,
          label: pn,
          render: (r) => {
            const cell = features[pn][r.feat];
            return h("span", null, [
              h("span", { class: `fdot f-${cell.color}` }),
              cell.value === true ? "Yes" : cell.value === false ? "No" : cell.value || "—",
            ]);
          },
        })),
      ),
      featKeys.map((f) => ({ feat: f })),
    ),
  );

  // Investment
  box.appendChild(h("h2.section-title", null, "Investment"));
  const invRows = [
    ["Appreciation", (v) => `${v.appreciation_pct}%`],
    ["Projected (3y)", (v) => inr(v.projected_value_3y)],
    ["Registration", (v) => inr(v.registration_cost)],
    ["Total investment", (v) => inr(v.total_investment)],
  ];
  const invNames = Object.keys(investment);
  box.appendChild(
    dataTable(
      [{ key: "metric", label: "Metric", render: (r) => r.metric }].concat(
        invNames.map((pn) => ({ key: pn, label: pn, num: true, render: (r) => r.vals[pn] })),
      ),
      invRows.map(([label, fn]) => ({
        metric: label,
        vals: Object.fromEntries(invNames.map((pn) => [pn, fn(investment[pn])])),
      })),
    ),
  );
  return box;
}

function cellRender(col, val) {
  if (val === null || val === undefined) return "—";
  if (col === "Status") return statusBadge(val);
  if (col === "Total Price" || col === "Price per sqft") return inr(val);
  if (col === "Area (sqft)") return Number(val).toLocaleString("en-IN");
  if (typeof val === "object") return JSON.stringify(val);
  return String(val);
}

async function brokersView() {
  const brokers = await api.brokers({ limit: 200 });
  const wrap = h("div", null, [
    h("div.title-row", null, [
      pageHead("Brokers", `${brokers.length} contacts`),
      h("button.btn", { onclick: openNewBroker }, "+ New broker"),
    ]),
  ]);
  if (!brokers.length) return wrap.appendChild(empty("No brokers yet — add one to start tracking.")), wrap;

  const perf = await Promise.all(brokers.map((b) => api.brokerPerformance(b.id).catch(() => null)));
  const rows = brokers.map((b, i) => ({ ...b, perf: perf[i] }));

  wrap.appendChild(
    dataTable(
      [
        { key: "name", label: "Broker" },
        { key: "phone", label: "Phone", render: (r) => r.phone || "—" },
        { key: "areas_covered", label: "Areas", render: (r) => r.areas_covered || "—" },
        { key: "shown", label: "Shown", num: true, render: (r) => (r.perf ? r.perf.shown_count : "—") },
        {
          key: "conv",
          label: "Conversion",
          num: true,
          render: (r) => (r.perf ? `${r.perf.conversion_rate}%` : "—"),
        },
        {
          key: "link",
          label: "",
          render: (r) =>
            h(
              "button.ghost-btn",
              { onclick: (e) => (e.stopPropagation(), openLinkBroker(r)) },
              "Link property",
            ),
        },
      ],
      rows,
    ),
  );
  return wrap;
}

// ---- write flows (forms) ----
function propertyFields(p = {}) {
  const feat = "yes / no / nearby";
  return [
    { name: "name", label: "Name", required: true, value: p.name },
    { name: "location", label: "Location", value: p.location },
    { name: "survey_number", label: "Survey number", value: p.survey_number },
    { name: "taluk", label: "Taluk", value: p.taluk },
    { name: "total_area_sqft", label: "Total area (sqft)", type: "number", value: p.total_area_sqft },
    { name: "asking_price", label: "Asking price (₹)", type: "number", value: p.asking_price },
    { name: "price_per_sqft", label: "Price / sqft (₹)", type: "number", value: p.price_per_sqft },
    { name: "status", label: "Status", type: "select", options: STATUSES, value: p.status },
    { name: "water_source", label: "Water source", value: p.water_source, placeholder: feat },
    { name: "electricity", label: "Electricity", value: p.electricity, placeholder: feat },
    { name: "road_access", label: "Road access", value: p.road_access, placeholder: feat },
    { name: "corner_plot", label: "Corner plot", type: "checkbox", value: p.corner_plot },
    { name: "notes", label: "Notes", type: "textarea", value: p.notes },
  ];
}

function openNewProperty() {
  formModal({
    title: "New property",
    fields: propertyFields(),
    submitLabel: "Create",
    onSubmit: async (v) => {
      const created = await api.createProperty(v);
      location.hash = `#/properties/${created.id}`;
      render();
    },
  });
}

function openEditProperty(p) {
  formModal({
    title: `Edit ${p.name}`,
    fields: propertyFields(p),
    onSubmit: async (v) => {
      await api.updateProperty(p.id, v);
      render();
    },
  });
}

function openAddSubdivision(id) {
  formModal({
    title: "Add subdivision",
    fields: [
      { name: "name", label: "Name", required: true },
      { name: "survey_number_full", label: "Full survey number" },
      { name: "area_sqft", label: "Area (sqft)", type: "number" },
    ],
    submitLabel: "Add",
    onSubmit: async (v) => {
      await api.addSubdivision(id, v);
      render();
    },
  });
}

function openAddNeighbor(id) {
  formModal({
    title: "Add neighbor",
    fields: [
      { name: "survey_number", label: "Survey number", required: true },
      { name: "direction", label: "Direction", type: "select", options: DIRECTIONS },
      { name: "shared_boundary", label: "Shares a boundary", type: "checkbox" },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
    submitLabel: "Add",
    onSubmit: async (v) => {
      await api.addNeighbor(id, v);
      render();
    },
  });
}

function openUploadDocument(id) {
  formModal({
    title: "Upload document",
    fields: [
      { name: "filename", label: "File name", required: true, placeholder: "patta_2024.pdf" },
      { name: "doc_type", label: "Type", type: "select", options: DOC_TYPES },
      { name: "issue_date", label: "Issue date", type: "date" },
    ],
    submitLabel: "Upload",
    onSubmit: async (v) => {
      await api.uploadDocument(id, v);
      render();
    },
  });
}

function openAddBoundary(id) {
  formModal({
    title: "Add survey boundary",
    fields: [
      {
        name: "vertices",
        label: "Vertices",
        type: "textarea",
        rows: 5,
        placeholder: "12.910, 79.130\n12.913, 79.134\n12.910, 79.137",
        help: "One 'lat, lng' per line — at least 3 points.",
      },
      { name: "label", label: "Label" },
      { name: "neighbor_survey_number", label: "Neighbor survey # (optional)" },
    ],
    submitLabel: "Save boundary",
    onSubmit: async (v) => {
      const vertices = parseVertices(v.vertices);
      if (vertices.length < 3) throw new Error("Enter at least 3 valid 'lat, lng' points.");
      const payload = { vertices };
      if (v.label) payload.label = v.label;
      if (v.neighbor_survey_number) payload.neighbor_survey_number = v.neighbor_survey_number;
      await api.addBoundary(id, payload);
      render();
    },
  });
}

function openNewBroker() {
  formModal({
    title: "New broker",
    fields: [
      { name: "name", label: "Name", required: true },
      { name: "phone", label: "Phone" },
      { name: "email", label: "Email" },
      { name: "areas_covered", label: "Areas", placeholder: "Thuthikadu, Katpadi", help: "Comma-separated." },
      { name: "commission_rate", label: "Commission %", type: "number" },
    ],
    submitLabel: "Create",
    onSubmit: async (v) => {
      await api.createBroker(v);
      render();
    },
  });
}

async function openLinkBroker(broker) {
  const props = await api.properties({ limit: 200 });
  formModal({
    title: `Link ${broker.name} to a property`,
    fields: [
      {
        name: "property_id",
        label: "Property",
        type: "select",
        options: props.map((p) => ({ value: String(p.id), label: p.name })),
      },
      { name: "asking_price", label: "Broker's asking price (₹)", type: "number" },
      { name: "shown_date", label: "Shown date", type: "date" },
      { name: "broker_notes", label: "Notes", type: "textarea" },
    ],
    submitLabel: "Link",
    onSubmit: async (v) => {
      const { property_id, ...terms } = v;
      await api.linkBroker(broker.id, property_id, terms);
      render();
    },
  });
}

function openNewPreference() {
  formModal({
    title: "New preference",
    fields: [
      { name: "name", label: "Name", required: true, placeholder: "My Ideal Plot" },
      { name: "budget_max", label: "Max budget (₹)", type: "number" },
      { name: "size_min_sqft", label: "Min size (sqft)", type: "number" },
      { name: "size_max_sqft", label: "Max size (sqft)", type: "number" },
      { name: "locations", label: "Preferred locations", help: "Comma-separated." },
      { name: "required_features", label: "Required features", help: "e.g. water_source, road_access" },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
    submitLabel: "Create",
    onSubmit: async (v) => {
      const payload = { ...v, locations: csv(v.locations), required_features: csv(v.required_features) };
      await api.createPreference(payload);
      location.hash = "#/recommendations?pref=" + encodeURIComponent(v.name);
      render();
    },
  });
}

// ---- small builders ----
function field(label, input) {
  return h("div.field", null, [h("label", null, label), input]);
}
function fact(label, value) {
  return h("div", null, [h("div.fact-label", null, label), h("div.fact-value", null, value)]);
}
function kv(k, v) {
  return h("div.kv", null, [h("span", null, k), h("span.muted", null, v)]);
}
function listCard(title, items, emptyMsg) {
  return h("div.card.card-pad", null, [
    h("div.tile-label", { style: "margin-bottom:12px" }, title),
    items.length ? h("div.kv-list", null, items) : empty(emptyMsg),
  ]);
}
function featureText(v) {
  return v ? titlecase(v) : "—";
}

// Render a GeoJSON FeatureCollection as an SVG (subject vs neighbor colored).
function boundarySvg(geo) {
  const pts = [];
  for (const f of geo.features) for (const ring of f.geometry.coordinates) for (const c of ring) pts.push(c);
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  const minX = Math.min(...xs),
    maxX = Math.max(...xs),
    minY = Math.min(...ys),
    maxY = Math.max(...ys);
  const W = 320,
    H = 240,
    pad = 16;
  const spanX = maxX - minX || 1,
    spanY = maxY - minY || 1;
  const sx = (x) => pad + ((x - minX) / spanX) * (W - 2 * pad);
  const sy = (y) => H - pad - ((y - minY) / spanY) * (H - 2 * pad); // flip Y

  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("class", "map-svg");
  for (const f of geo.features) {
    const neighbor = f.properties.role === "neighbor";
    for (const ring of f.geometry.coordinates) {
      const poly = document.createElementNS(svgNS, "polygon");
      poly.setAttribute("points", ring.map((c) => `${sx(c[0]).toFixed(1)},${sy(c[1]).toFixed(1)}`).join(" "));
      poly.setAttribute("fill", neighbor ? "rgba(235,104,52,0.18)" : "rgba(42,120,214,0.22)");
      poly.setAttribute("stroke", neighbor ? "#eb6834" : "#2a78d6");
      poly.setAttribute("stroke-width", "2");
      poly.setAttribute("stroke-linejoin", "round");
      svg.appendChild(poly);
    }
  }
  const legend = h("div", { style: "display:flex;gap:16px;margin-top:10px;font-size:12px" }, [
    h("span", null, [h("span", { class: "fdot", style: "background:#2a78d6" }), " Subject"]),
    h("span", null, [h("span", { class: "fdot", style: "background:#eb6834" }), " Neighbor"]),
  ]);
  return h("div", null, [svg, legend]);
}

// ---- utils ----
function readQuery() {
  const q = (location.hash.split("?")[1] || "").trim();
  return Object.fromEntries(new URLSearchParams(q).entries());
}

// ---- chrome: theme, settings, connection ----
function initTheme() {
  const saved = localStorage.getItem("landseer_theme");
  if (saved) document.documentElement.setAttribute("data-theme", saved);
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme");
    const isDark = cur ? cur === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    const next = isDark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("landseer_theme", next);
  });
}

function initSettings() {
  document.getElementById("settings-btn").addEventListener("click", () => {
    const base = h("input", { type: "text", value: getBase(), placeholder: "(same origin)", style: "width:100%" });
    const token = h("input", { type: "password", value: getToken(), placeholder: "bearer token (optional)", style: "width:100%" });
    const root = document.getElementById("modal-root");
    const close = () => clear(root);
    root.appendChild(
      h("div.modal-scrim", { onclick: (e) => e.target.classList.contains("modal-scrim") && close() }, [
        h("div.modal", null, [
          h("h3", null, "Connection settings"),
          field("API base URL", base),
          h("div", { style: "height:10px" }),
          field("API token", token),
          h("div.row", null, [
            h("button.ghost-btn", { onclick: close }, "Cancel"),
            h(
              "button.btn",
              {
                onclick: () => {
                  setBase(base.value.trim());
                  setToken(token.value.trim());
                  close();
                  checkConnection();
                  render();
                },
              },
              "Save",
            ),
          ]),
        ]),
      ]),
    );
  });
}

async function checkConnection() {
  try {
    await api.health();
    connEl.className = "conn ok";
    connEl.textContent = "connected";
  } catch {
    connEl.className = "conn err";
    connEl.textContent = "offline";
  }
}

// ---- boot ----
initTheme();
initSettings();
checkConnection();
if (!location.hash) location.hash = "#/";
render();
