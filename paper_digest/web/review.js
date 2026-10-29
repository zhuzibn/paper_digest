"use strict";

const token = location.hash.slice(1);
const papersElement = document.querySelector("#papers");
const saveButton = document.querySelector("#save");
const message = document.querySelector("#save-message");
const choices = new Map();
const rows = new Map();
let saving = false;

const sourceNames = {
  arxiv: "arXiv", nature: "Nature Communications", "nature-journal": "Nature",
  "aps-prl": "Physical Review Letters", "aps-prb": "Physical Review B",
  "aps-prapplied": "Physical Review Applied", "aps-prx": "Physical Review X",
  "aps-rmp": "Reviews of Modern Physics", "aip-apl": "Applied Physics Letters",
};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function updateSummary() {
  const accepted = [...choices.values()].filter(value => value === "accepted").length;
  const skipped = choices.size - accepted;
  document.querySelector("#selection-summary").textContent = choices.size
    ? `${accepted} to accept · ${skipped} to skip`
    : "No unsaved decisions";
  saveButton.disabled = saving || choices.size === 0;
}

function markSaved(id, decision) {
  const row = rows.get(id);
  if (!row) return;
  row.dataset.saved = "true";
  row.querySelectorAll("input").forEach(input => {
    input.checked = input.value === decision;
    input.disabled = true;
  });
  row.querySelector(".row-status").textContent = `Saved · ${decision === "accepted" ? "Accepted" : "Skipped"}`;
  choices.delete(id);
}

function renderPaper(paper) {
  const row = element("article", "paper");
  row.dataset.id = paper.id;
  row.append(element("span", "number", String(paper.number).padStart(2, "0")));
  const content = element("div", "paper-content");
  const meta = element("div", "paper-meta");
  meta.append(element("span", "source", sourceNames[paper.source] || paper.source));
  meta.append(element("span", "", paper.published_date || "Publication date unknown"));
  const title = element("h2");
  title.id = `title-${paper.id}`;
  // Treat stored titles as text and only make HTTP(S) source links clickable.
  try {
    const url = new URL(paper.link);
    if (!["https:", "http:"].includes(url.protocol)) throw new Error("Unsupported link");
    const link = element("a", "", paper.title);
    link.href = url.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    title.append(link);
  } catch {
    title.textContent = paper.title;
  }
  content.append(meta, title);
  if (paper.authors.length) content.append(element("p", "authors", paper.authors.join("; ")));
  content.append(element("p", "paper-id", paper.id));
  const keywords = element("div", "keywords");
  keywords.append(element("span", "", "Matched:"));
  if (!paper.keywords_matched.length) keywords.append(element("span", "", "Not recorded"));
  paper.keywords_matched.forEach(keyword => keywords.append(element("span", "keyword", keyword)));
  content.append(keywords);
  const area = element("div", "choice-area");
  const fieldset = element("fieldset");
  fieldset.setAttribute("aria-labelledby", title.id);
  fieldset.append(element("legend", "", "Your decision"));
  const controls = element("div", "choices");
  for (const [value, label] of [["pending", "Leave pending"], ["accepted", "Accept"], ["skipped", "Skip"]]) {
    const wrapper = element("label", "choice");
    const input = element("input");
    input.type = "radio";
    input.name = paper.id;
    input.value = value;
    input.checked = value === "pending";
    input.addEventListener("change", () => {
      if (value === "pending") choices.delete(paper.id);
      else choices.set(paper.id, value);
      row.querySelector(".row-status").textContent = value === "pending" ? "Stays pending" : "Not saved yet";
      updateSummary();
    });
    wrapper.append(input, element("span", "", label));
    controls.append(wrapper);
  }
  fieldset.append(controls);
  area.append(fieldset, element("p", "row-status", "Stays pending"));
  row.append(content, area);
  rows.set(paper.id, row);
  if (paper.decision !== "pending") markSaved(paper.id, paper.decision);
  return row;
}

async function loadPapers() {
  try {
    const response = await fetch("/api/papers", {headers: {"X-Review-Token": token}});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    document.querySelector("#total").textContent = data.papers.length;
    papersElement.replaceChildren(...data.papers.map(renderPaper));
    if (!data.papers.length) papersElement.append(element("p", "empty", "No pending papers to review."));
  } catch (error) {
    papersElement.replaceChildren();
    const notice = document.querySelector("#load-error");
    notice.hidden = false;
    notice.textContent = `Could not load papers. ${error.message} Keep the review server running, then reload this page.`;
  }
}

saveButton.addEventListener("click", async () => {
  if (saving || !choices.size) return;
  saving = true;
  updateSummary();
  rows.forEach(row => row.querySelectorAll("input").forEach(input => { input.disabled = true; }));
  message.dataset.error = "false";
  message.textContent = "Saving your decisions…";
  const decisions = [...choices].map(([id, decision]) => ({id, decision}));
  try {
    const response = await fetch("/api/decisions", {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-Review-Token": token},
      body: JSON.stringify({decisions}),
    });
    const data = await response.json();
    (data.saved || []).forEach(item => markSaved(item.id, item.decision));
    if (!response.ok) throw new Error(`${data.saved?.length || 0} decisions confirmed. ${data.error}`);
    const pending = [...rows.values()].filter(row => row.dataset.saved !== "true").length;
    message.textContent = `Saved ${data.saved.length} decisions. ${pending} papers in this review remain pending.`;
  } catch (error) {
    message.dataset.error = "true";
    message.textContent = `Save not fully confirmed. ${error.message} Unsaved choices are kept here; retry after resolving the problem.`;
  } finally {
    saving = false;
    rows.forEach(row => {
      if (row.dataset.saved !== "true") row.querySelectorAll("input").forEach(input => { input.disabled = false; });
    });
    updateSummary();
  }
});

window.addEventListener("beforeunload", event => {
  if (choices.size) {
    event.preventDefault();
    event.returnValue = "";
  }
});

loadPapers();
