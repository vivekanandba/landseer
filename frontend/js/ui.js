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
