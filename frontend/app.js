const state = {
  review: null,
  sessionHash: `browser-${crypto.randomUUID()}`,
  approvalKey: crypto.randomUUID(),
  requestKey: crypto.randomUUID(),
};

const consent = document.querySelector("#consent");
const authorizeButton = document.querySelector("#authorize-button");
const reserveButton = document.querySelector("#reserve-button");
const recoveryButton = document.querySelector("#recovery-button");
const actionMessage = document.querySelector("#action-message");
const statusTitle = document.querySelector("#status-title");
const statusCopy = document.querySelector("#status-copy");
const progressItems = [...document.querySelectorAll(".progress li")];

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
    statusTitle.textContent = "Authorization required";
    statusCopy.textContent = "The reviewed plan is preserved. Authorize it again to continue.";
    actionMessage.textContent = "No reservation was created.";
    return;
  }
  if (error.code === "INVENTORY_UNAVAILABLE" || error.code === "PLAN_CHANGED") {
    statusTitle.textContent = "Plan needs review";
    statusCopy.textContent = "Availability or the exact plan changed. Nothing was partially reserved.";
    actionMessage.textContent = error.message;
    showRecovery("Refresh plan", () => window.location.reload());
    return;
  }
  if (error.code === "NETWORK_INTERRUPTION") {
    statusTitle.textContent = "Reservation status unknown";
    statusCopy.textContent = "Keep this request open; retrying safely checks the same reservation request.";
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

function titleCase(value) {
  return value.replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
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

document.querySelector("#coordinate-button").addEventListener("click", async (event) => {
  setBusy(event.currentTarget, true, "Coordinating…", "Coordinate offsite");
  document.querySelector("#brief-panel").hidden = true;
  document.querySelector("#coordination").hidden = false;
  setStep(1);
  try {
    const result = await request("/product/api/coordinate?mode=live", {
      method: "POST",
      body: JSON.stringify({ session_hash: state.sessionHash }),
    });
    if (!result.findings.length) throw new Error("No validation findings were returned.");
    state.review = await request(`/product/api/review?session_hash=${encodeURIComponent(state.sessionHash)}`);
    document.querySelector("#plan-id").textContent = state.review.plan_hash.slice(0, 12);
    renderReview(state.review);
    const traceItems = [...document.querySelectorAll("[data-trace]")];
    const shortMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const delay = shortMotion ? 20 : 360;
    for (const item of traceItems) {
      item.classList.add("active");
      await new Promise((resolve) => window.setTimeout(resolve, delay));
      item.classList.remove("active");
      item.classList.add("complete");
    }
    document.querySelector("#coordination").hidden = true;
    document.querySelector("#issues").hidden = false;
    const traceMode = document.querySelector("#trace-mode");
    if (result.agent_mode === "gemini_adk") {
      traceMode.textContent = "Gemini on Vertex AI completed the proposal through Google ADK.";
    } else {
      traceMode.textContent = "The live agent was unavailable, so the verified deterministic demo path was preserved.";
    }
    document.querySelector("#issues-title").focus?.();
  } catch (error) {
    document.querySelector("#coordination-title").textContent = "Coordination paused";
    const message = document.createElement("p");
    message.textContent = `${error.message} Nothing has been reserved.`;
    document.querySelector("#coordination").append(message);
  }
});

document.querySelector("#apply-fixes").addEventListener("click", () => {
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
    const expires = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" }).format(new Date(approval.expires_at));
    statusTitle.textContent = `Authorized until ${expires}`;
    statusCopy.textContent = "The exact reviewed plan may now create three simulated reservations.";
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
    statusTitle.textContent = "Confirmed";
    statusCopy.textContent = "Three simulated reservations were created atomically.";
    actionMessage.textContent = "Already completed requests safely return this same ledger.";
    document.querySelector("#confirmation").hidden = false;
    document.querySelector("#confirmation").scrollIntoView({ behavior: "smooth", block: "center" });
    setStep(4);
  } catch (error) {
    handleReservationFailure(error);
    reserveButton.disabled = false;
  }
});
