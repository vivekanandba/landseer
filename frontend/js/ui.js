// Tiny DOM helpers and shared formatters/widgets. No framework.

// h("div.card", {onclick}, [children]) -> HTMLElement
export function h(tagSpec, props = null, children = null) {
  const [tag, ...classes] = tagSpec.split(".");
  const el = document.createElement(tag || "div");
  if (classes.length) el.className = classes.join(" ");
  if (props) {
    for (const [k, v] of Object.entries(props)) {
      if (v === null || v === undefined) continue;
      if (k === "class") el.className = [el.className, v].filter(Boolean).join(" ");
      else if (k === "html") el.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
      else if (k === "dataset") Object.assign(el.dataset, v);
      else el.setAttribute(k, v);
    }
  }
  append(el, children);
  return el;
}

function append(el, children) {
  if (children === null || children === undefined) return;
  if (Array.isArray(children)) children.forEach((c) => append(el, c));
  else if (children instanceof Node) el.appendChild(children);
  else el.appendChild(document.createTextNode(String(children)));
}

export function clear(el) {
  el.replaceChildren();
  return el;
}

// ---- formatters ----
export function inr(n) {
  if (n === null || n === undefined) return "—";
  const v = Number(n);
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(2)} L`;
  return `₹${v.toLocaleString("en-IN")}`;
}
export function sqft(n) {
  if (n === null || n === undefined) return "—";
  return `${Number(n).toLocaleString("en-IN")} sqft`;
}
export function titlecase(s) {
  return (s || "").replace(/\b\w/g, (c) => c.toUpperCase()).replace(/_/g, " ");
}

// ---- shared widgets ----
export function statusBadge(status) {
  return h("span", { class: `badge b-${status}` }, titlecase(status));
}

export function docBadge(status) {
  return h("span", { class: `badge b-${status}` }, titlecase(status));
}

export function meter(score) {
  const pct = Math.max(0, Math.min(100, Number(score) || 0));
  return h("div.meter", null, [
    h("div.meter-track", null, [h("div.meter-fill", { style: `width:${pct}%` })]),
    h("span.meter-val", null, `${Math.round(pct)}`),
  ]);
}

export function spinner(msg = "Loading…") {
  return h("div.spinner", null, msg);
}
export function empty(msg) {
  return h("div.empty", null, msg);
}
export function errorBanner(msg) {
  return h("div.banner-err", null, msg);
}

export function tile(label, value, foot, accent = true) {
  return h("div", { class: "card tile" + (accent ? " tile-accent" : "") }, [
    h("div.tile-label", null, label),
    h("div.tile-value", null, value),
    foot ? h("div.tile-foot", null, foot) : null,
  ]);
}

// Build an <table class="data"> from columns + rows.
// columns: [{key, label, num?, render?(row)}]; onRow optional click handler.
export function dataTable(columns, rows, onRow) {
  const thead = h("thead", null, [
    h(
      "tr",
      null,
      columns.map((c) => h("th", { class: c.num ? "num" : null }, c.label)),
    ),
  ]);
  const tbody = h(
    "tbody",
    null,
    rows.map((row) => {
      const tr = h("tr", { class: onRow ? "clickable" : null }, [
        ...columns.map((c) =>
          h("td", { class: c.num ? "num" : null }, c.render ? c.render(row) : fmtCell(row[c.key])),
        ),
      ]);
      if (onRow) tr.addEventListener("click", () => onRow(row));
      return tr;
    }),
  );
  return h("div.table-wrap", null, [h("table.data", null, [thead, tbody])]);
}

function fmtCell(v) {
  if (v === null || v === undefined) return "—";
  return String(v);
}

// ---- modal + form ----
// Show a node in a centered modal; returns a close() fn. One modal at a time.
export function modal(contentNode) {
  const root = document.getElementById("modal-root");
  const close = () => clear(root);
  root.replaceChildren(
    h(
      "div.modal-scrim",
      { onclick: (e) => e.target.classList.contains("modal-scrim") && close() },
      [contentNode],
    ),
  );
  return close;
}

// Declarative form modal.
// fields: [{name, label, type?, options?, value?, required?, placeholder?, rows?, help?}]
//   type ∈ text|number|date|password|select|textarea|checkbox (default text)
// onSubmit(values) is async; throw to show an inline error and keep the modal open.
// Empty optional fields are omitted; number fields are coerced to Number.
export function formModal({ title, fields, submitLabel = "Save", onSubmit }) {
  const entries = {};
  const body = fields.map((f) => {
    let input;
    if (f.type === "select") {
      input = h(
        "select",
        { style: "width:100%" },
        (f.options || []).map((o) => {
          const value = typeof o === "string" ? o : o.value;
          const label = typeof o === "string" ? o : o.label;
          return h("option", { value }, label);
        }),
      );
      if (f.value != null) input.value = f.value;
    } else if (f.type === "textarea") {
      input = h("textarea", { rows: f.rows || 3, placeholder: f.placeholder || "" }, f.value || "");
    } else if (f.type === "checkbox") {
      input = h("input", { type: "checkbox" });
      if (f.value) input.checked = true;
    } else {
      input = h("input", {
        type: f.type || "text",
        placeholder: f.placeholder || "",
        value: f.value != null ? f.value : "",
        style: "width:100%",
      });
    }
    entries[f.name] = { input, f };
    if (f.type === "checkbox") {
      return h("label", { class: "form-check" }, [input, f.label]);
    }
    return h("div.field", { style: "margin-bottom:12px" }, [
      h("label", null, f.label + (f.required ? " *" : "")),
      input,
      f.help ? h("div.muted", { style: "font-size:12px" }, f.help) : null,
    ]);
  });

  const err = h("div");
  const submitBtn = h("button.btn", null, submitLabel);
  const close = modal(
    h("div.modal", null, [
      h("h3", null, title),
      err,
      h("div", null, body),
      h("div.row", null, [h("button.ghost-btn", { onclick: () => close() }, "Cancel"), submitBtn]),
    ]),
  );

  submitBtn.addEventListener("click", async () => {
    const values = {};
    for (const [name, { input, f }] of Object.entries(entries)) {
      let v = f.type === "checkbox" ? input.checked : input.value.trim();
      if (f.required && (v === "" || v === null || v === undefined)) {
        clear(err).appendChild(errorBanner(`${f.label} is required`));
        return;
      }
      if (v === "" && f.type !== "checkbox") continue; // omit empty optionals
      if (f.type === "number") v = Number(v);
      values[name] = v;
    }
    submitBtn.disabled = true;
    try {
      await onSubmit(values);
      close();
    } catch (e) {
      submitBtn.disabled = false;
      clear(err).appendChild(errorBanner(e.message || "Request failed"));
    }
  });
  return close;
}
