const state = {
  review: null,
  sessionHash: `browser-${crypto.randomUUID()}`,
  approvalKey: crypto.randomUUID(),
  requestKey: crypto.randomUUID(),
  coordinatedAt: null,
  validatedAt: null,
  approval: null,
  ledger: null,
};

const consent = document.querySelector("#consent");
const authorizeButton = document.querySelector("#authorize-button");
const reserveButton = document.querySelector("#reserve-button");
const recoveryButton = document.querySelector("#recovery-button");
const actionMessage = document.querySelector("#action-message");
const statusTitle = document.querySelector("#status-title");
const statusCopy = document.querySelector("#status-copy");
const progressItems = [...document.querySelectorAll(".progress li")];
const coordinateButton = document.querySelector("#coordinate-button");
const coordination = document.querySelector("#coordination");
const coordinationRetry = document.querySelector("#coordination-retry");
const coordinationError = document.querySelector("#coordination-error");

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch (cause) {
    throw new ApiError("NETWORK_INTERRUPTION", "The connection was interrupted.", cause);
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body.detail;
    throw new ApiError(
      detail?.code || "REQUEST_FAILED",
      detail?.message || (typeof detail === "string" ? detail : "The request could not be completed."),
    );
  }
  return body;
}

class ApiError extends Error {
  constructor(code, message, cause) {
    super(message, { cause });
    this.name = "ApiError";
    this.code = code;
  }
}

function showRecovery(label, handler) {
  recoveryButton.textContent = label;
  recoveryButton.hidden = false;
  recoveryButton.onclick = handler;
}

function resetAuthorization() {
  reserveButton.hidden = true;
  authorizeButton.hidden = false;
  consent.parentElement.hidden = false;
  consent.checked = false;
  authorizeButton.disabled = true;
  state.approvalKey = crypto.randomUUID();
  setStep(2);
}

function handleReservationFailure(error) {
  if (error.code === "AUTHORIZATION_EXPIRED" || error.code === "AUTHORIZATION_REQUIRED") {
    resetAuthorization();
    setStatus("warning", "Authorization required", "The reviewed plan is preserved. Authorize it again to continue.");
    actionMessage.textContent = "No reservation was created.";
    return;
  }
  if (error.code === "INVENTORY_UNAVAILABLE" || error.code === "PLAN_CHANGED") {
    setStatus("warning", "Plan needs review", "Availability or the exact plan changed. Nothing was partially reserved.");
    actionMessage.textContent = error.message;
    showRecovery("Refresh plan", () => window.location.reload());
    return;
  }
  if (error.code === "NETWORK_INTERRUPTION") {
    setStatus("warning", "Reservation status unknown", "Keep this request open; retrying safely checks the same reservation request.");
    actionMessage.textContent = "The connection was interrupted. Do not start a new plan.";
    showRecovery("Check reservation status", () => reserveButton.click());
    return;
  }
  actionMessage.textContent = `${error.message} Nothing was partially reserved.`;
}

function setBusy(button, busy, busyLabel, idleLabel) {
  button.disabled = busy;
  button.textContent = busy ? busyLabel : idleLabel;
}

function setStep(index) {
  progressItems.forEach((item, itemIndex) => {
    item.classList.toggle("complete", itemIndex < index);
    item.classList.toggle("current", itemIndex === index);
    if (itemIndex === index) item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
  });
}

function setStatus(kind, title, copy) {
  document.querySelector("#review-status").dataset.status = kind;
  statusTitle.textContent = title;
  statusCopy.textContent = copy;
}

function titleCase(value) {
  return value.replaceAll(/[-_]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatTime(value) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function renderHandoff(ledger) {
  const attendees = new Map(state.review.brief.attendees.map((person) => [person.id, person.name]));
  const sessions = new Map(state.review.plan.agenda.map((session) => [session.id, session.title]));
  document.querySelector("#preparation-list").replaceChildren(
    ...state.review.plan.preparation.map((task) => {
      const item = document.createElement("li");
      const artifact = document.createElement("strong");
      const detail = document.createElement("span");
      artifact.textContent = task.artifact;
      detail.textContent = `${attendees.get(task.owner_attendee_id)} · ${sessions.get(task.session_id)} · due Oct 9`;
      item.append(artifact, detail);
      return item;
    }),
  );

  const auditEvents = [
    ["Coordinated", state.coordinatedAt],
    ["Deterministic checks passed", state.validatedAt],
    ["Exact plan authorized", state.approval?.authorized_at],
    ["Simulated reservations confirmed", state.confirmedAt],
  ];
  document.querySelector("#audit-list").replaceChildren(...auditEvents.map(([label, timestamp]) => {
    const item = document.createElement("li");
    const event = document.createElement("strong");
    const time = document.createElement("span");
    event.textContent = label;
    time.textContent = formatTime(timestamp);
    item.append(event, time);
    return item;
  }));

  document.querySelector("#record-plan-id").textContent = state.review.plan_hash;
  document.querySelector("#record-approval-id").textContent = state.approval.id;
  document.querySelector("#record-scope").textContent = state.approval.authorized_actions.map(titleCase).join(", ");
  document.querySelector("#record-expiry").textContent = new Date(state.approval.expires_at).toLocaleString();
}

function confirmationSummary() {
  const attendees = new Map(state.review.brief.attendees.map((person) => [person.id, person.name]));
  const confirmations = state.ledger.reservations
    .map((item) => `${titleCase(item.inventory_id)}: ${item.confirmation_id}`)
    .join("\n");
  const preparation = state.review.plan.preparation
    .map((task) => `${task.artifact}: ${attendees.get(task.owner_attendee_id)}, due Oct 9`)
    .join("\n");
  return `Offsite Captain confirmation\nNew York · October 12–14, 2026\nPlan ${state.review.plan_hash}\n\nSimulated reservations\n${confirmations}\n\nPreparation\n${preparation}`;
}

function renderReview(review) {
  const totalCents = review.plan.inventory.reduce(
    (sum, selection) => sum + selection.quantity * selection.unit_cost_cents,
    0,
  );
  const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  const total = money.format(totalCents / 100);
  document.querySelector("#budget-total").textContent = total;
  document.querySelector("#budget-detail").textContent = `${money.format((review.brief.budget_cents - totalCents) / 100)} under budget`;
  document.querySelector("#authorization-total").textContent = total;
  document.querySelector("#confirmation-total").textContent = total;
  const attendeeNames = new Map(review.brief.attendees.map((attendee) => [attendee.id, attendee.name]));
  const grouped = new Map();
  for (const session of review.plan.agenda) {
    const date = session.starts_at.slice(0, 10);
    if (!grouped.has(date)) grouped.set(date, []);
    grouped.get(date).push(session);
  }
  const agendaDays = document.querySelector("#agenda-days");
  agendaDays.replaceChildren(...[...grouped.entries()].map(([date, sessions]) => {
    const day = document.createElement("div");
    day.className = "day";
    const heading = document.createElement("div");
    heading.className = "day-heading";
    const dayName = document.createElement("strong");
    dayName.textContent = new Intl.DateTimeFormat("en-US", { weekday: "long", month: "short", day: "numeric", timeZone: review.brief.timezone }).format(new Date(`${date}T12:00:00-04:00`));
    const zone = document.createElement("span");
    zone.textContent = review.brief.timezone;
    heading.append(dayName, zone);
    day.append(heading);
    for (const session of sessions) {
      const article = document.createElement("article");
      article.className = `session${session.id === "activity" ? " activity" : ""}`;
      const time = document.createElement("time");
      time.textContent = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: review.brief.timezone }).format(new Date(session.starts_at));
      const detail = document.createElement("div");
      const title = document.createElement("h3");
      title.textContent = session.title;
      const people = session.required_attendee_ids.length === review.brief.attendees.length
        ? "All attendees"
        : session.required_attendee_ids.map((id) => attendeeNames.get(id)).join(", ");
      const room = session.room_inventory_id ? titleCase(session.room_inventory_id) : titleCase(session.title);
      const durationHours = (new Date(session.ends_at) - new Date(session.starts_at)) / 3600000;
      const meta = document.createElement("p");
      meta.textContent = `${people} · ${room} · ${durationHours} ${durationHours === 1 ? "hour" : "hours"}`;
      const ready = document.createElement("span");
      ready.className = "check";
      ready.textContent = "Ready";
      detail.append(title, meta);
      article.append(time, detail, ready);
      day.append(article);
    }
    return day;
  }));

  const commitments = document.querySelector("#commitment-list");
  commitments.replaceChildren(...review.plan.inventory.map((selection) => {
    const row = document.createElement("div");
    const name = document.createElement("dt");
    const quantity = document.createElement("dd");
    const cost = document.createElement("dd");
    name.textContent = titleCase(selection.inventory_id);
    quantity.textContent = `${selection.quantity} ${selection.kind === "hotel" ? "room nights" : selection.kind === "room" ? "meeting days" : "attendees"}`;
    cost.textContent = money.format(selection.quantity * selection.unit_cost_cents / 100);
    row.append(name, quantity, cost);
    return row;
  }));
  const owners = new Set(review.plan.preparation.map((task) => task.owner_attendee_id));
  document.querySelector("#preparation-summary").textContent = `${review.plan.preparation.length} documents · ${owners.size} owners · Due Oct 9`;
}

async function coordinateOffsite(trigger) {
  const idleLabel = trigger === coordinateButton ? "Coordinate offsite" : "Try coordination again";
  setBusy(trigger, true, "Coordinating…", idleLabel);
  document.querySelector("#brief-panel").hidden = true;
  coordination.hidden = false;
  coordination.setAttribute("aria-busy", "true");
  coordinationRetry.hidden = true;
  coordinationError.hidden = true;
  document.querySelector("#coordination-title").textContent = "Building one feasible plan";
  const traceItems = [...document.querySelectorAll("[data-trace]")];
  traceItems.forEach((item) => {
    item.classList.remove("active", "complete");
    item.querySelector(".trace-state").textContent = "Waiting";
  });
  traceItems[0].classList.add("active");
  traceItems[0].querySelector(".trace-state").textContent = "In progress";
  setStep(1);
  try {
    const result = await request("/product/api/coordinate?mode=live", {
      method: "POST",
      body: JSON.stringify({ session_hash: state.sessionHash }),
    });
    if (!result.findings.length) throw new Error("No validation findings were returned.");
    state.review = await request(`/product/api/review?session_hash=${encodeURIComponent(state.sessionHash)}`);
    state.coordinatedAt = new Date().toISOString();
    document.querySelector("#plan-id").textContent = state.review.plan_hash.slice(0, 12);
    renderReview(state.review);
    for (const item of traceItems) {
      item.classList.remove("active");
      item.classList.add("complete");
      item.querySelector(".trace-state").textContent = "Complete";
    }
    coordination.setAttribute("aria-busy", "false");
    coordination.hidden = true;
    document.querySelector("#issues").hidden = false;
    const traceMode = document.querySelector("#trace-mode");
    if (result.agent_mode === "gemini_adk") {
      traceMode.textContent = "Gemini on Vertex AI completed the proposal through Google ADK.";
    } else {
      traceMode.textContent = "The live agent was unavailable, so the verified deterministic demo path was preserved.";
    }
    document.querySelector("#issues-title").focus?.();
  } catch (error) {
    coordination.setAttribute("aria-busy", "false");
    document.querySelector("#coordination-title").textContent = "Coordination paused";
    coordinationError.textContent = `${error.message} Nothing has been reserved.`;
    coordinationError.hidden = false;
    coordinationRetry.hidden = false;
    setBusy(trigger, false, "Coordinating…", idleLabel);
    coordinationRetry.focus();
  }
}

coordinateButton.addEventListener("click", () => coordinateOffsite(coordinateButton));
coordinationRetry.addEventListener("click", () => coordinateOffsite(coordinationRetry));

document.querySelector("#apply-fixes").addEventListener("click", () => {
  state.validatedAt = new Date().toISOString();
  document.querySelector("#issues").hidden = true;
  document.querySelector("#review-status").hidden = false;
  document.querySelector("#plan-layout").hidden = false;
  document.querySelector("#authorization").hidden = false;
  document.querySelector("#budget-label").textContent = "Plan total";
  setStep(2);
  document.querySelector("#review-status").scrollIntoView({ behavior: "smooth", block: "start" });
});

document.querySelector("#show-evidence").addEventListener("click", (event) => {
  const evidence = document.querySelector("#evidence");
  const expanded = event.currentTarget.getAttribute("aria-expanded") === "true";
  event.currentTarget.setAttribute("aria-expanded", String(!expanded));
  event.currentTarget.textContent = expanded ? "View validation evidence" : "Hide validation evidence";
  evidence.hidden = expanded;
});

consent.addEventListener("change", () => {
  authorizeButton.disabled = !consent.checked || !state.review;
});

authorizeButton.addEventListener("click", async () => {
  recoveryButton.hidden = true;
  setBusy(authorizeButton, true, "Authorizing exact plan…", "Authorize plan");
  actionMessage.textContent = "";
  try {
    const approval = await request("/product/api/authorize", {
      method: "POST",
      body: JSON.stringify({
        session_hash: state.sessionHash,
        plan_hash: state.review.plan_hash,
        idempotency_key: state.approvalKey,
      }),
    });
    state.approval = { ...approval, authorized_at: new Date().toISOString() };
    const expires = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" }).format(new Date(approval.expires_at));
    setStatus("info", `Authorized until ${expires}`, "The exact reviewed plan may now create three simulated reservations.");
    actionMessage.textContent = "Authorization recorded. No reservation exists yet.";
    authorizeButton.hidden = true;
    consent.parentElement.hidden = true;
    reserveButton.hidden = false;
    setStep(3);
  } catch (error) {
    actionMessage.textContent = error.message;
    authorizeButton.disabled = false;
  }
});

reserveButton.addEventListener("click", async () => {
  recoveryButton.hidden = true;
  setBusy(reserveButton, true, "Creating reservations…", "Create 3 reservations");
  actionMessage.textContent = "One atomic request is in progress.";
  try {
    const ledger = await request("/product/api/reserve", {
      method: "POST",
      body: JSON.stringify({
        session_hash: state.sessionHash,
        plan_hash: state.review.plan_hash,
        request_key: state.requestKey,
      }),
    });
    state.ledger = ledger;
    state.confirmedAt = new Date().toISOString();
    const ledgerElement = document.querySelector("#confirmation-ledger");
    ledgerElement.replaceChildren(...ledger.reservations.map((reservation) => {
      const article = document.createElement("article");
      const name = document.createElement("strong");
      const confirmation = document.createElement("p");
      name.textContent = reservation.inventory_id.replaceAll("-", " ");
      confirmation.textContent = `Confirmation ${reservation.confirmation_id}`;
      article.append(name, confirmation);
      return article;
    }));
    setStatus("success", "Confirmed", "Three simulated reservations were created atomically.");
    actionMessage.textContent = "Already completed requests safely return this same ledger.";
    document.querySelector("#confirmation").hidden = false;
    renderHandoff(ledger);
    document.querySelector("#confirmation").scrollIntoView({ behavior: "smooth", block: "center" });
    setStep(4);
  } catch (error) {
    handleReservationFailure(error);
    reserveButton.disabled = false;
  }
});

document.querySelector("#open-plan-button").addEventListener("click", () => {
  document.querySelector("#agenda-title").scrollIntoView({ behavior: "smooth", block: "start" });
  document.querySelector("#agenda-title").focus?.();
});

document.querySelector("#copy-summary-button").addEventListener("click", async (event) => {
  const handoffMessage = document.querySelector("#handoff-message");
  try {
    await navigator.clipboard.writeText(confirmationSummary());
    event.currentTarget.textContent = "Summary copied";
    handoffMessage.textContent = "Confirmation summary copied to the clipboard.";
  } catch {
    event.currentTarget.textContent = "Copy unavailable";
    handoffMessage.textContent = "The browser could not access the clipboard. The confirmation details remain visible above.";
  }
  window.setTimeout(() => { event.currentTarget.textContent = "Copy confirmation summary"; }, 2000);
});

document.querySelector("#authorization-record-button").addEventListener("click", (event) => {
  const record = document.querySelector("#authorization-record");
  const expanded = event.currentTarget.getAttribute("aria-expanded") === "true";
  event.currentTarget.setAttribute("aria-expanded", String(!expanded));
  event.currentTarget.textContent = expanded ? "View authorization record" : "Hide authorization record";
  record.hidden = expanded;
});
