const state = {
  review: null,
  sessionHash: `browser-${crypto.randomUUID()}`,
  approvalKey: crypto.randomUUID(),
  requestKey: crypto.randomUUID(),
};

const consent = document.querySelector("#consent");
const authorizeButton = document.querySelector("#authorize-button");
const reserveButton = document.querySelector("#reserve-button");
const actionMessage = document.querySelector("#action-message");
const statusTitle = document.querySelector("#status-title");
const statusCopy = document.querySelector("#status-copy");
const progressItems = [...document.querySelectorAll(".progress li")];

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const body = await response.json();
  if (!response.ok) {
    const detail = body.detail?.message || body.detail || "The request could not be completed.";
    throw new Error(detail);
  }
  return body;
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

document.querySelector("#coordinate-button").addEventListener("click", async (event) => {
  setBusy(event.currentTarget, true, "Coordinating…", "Coordinate offsite");
  document.querySelector("#brief-panel").hidden = true;
  document.querySelector("#coordination").hidden = false;
  setStep(1);
  try {
    const result = await request("/product/api/coordinate", { method: "POST" });
    if (!result.findings.length) throw new Error("No validation findings were returned.");
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
  document.querySelector("#budget-total").textContent = "$7,940";
  document.querySelector("#budget-detail").textContent = "$560 under budget";
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
    actionMessage.textContent = `${error.message} Nothing was partially reserved.`;
    reserveButton.disabled = false;
  }
});

request("/product/api/review")
  .then((review) => {
    state.review = review;
    document.querySelector("#plan-id").textContent = review.plan_hash.slice(0, 12);
    authorizeButton.disabled = !consent.checked;
  })
  .catch((error) => {
    statusTitle.textContent = "Plan unavailable";
    statusCopy.textContent = "The reviewed plan could not be loaded.";
    actionMessage.textContent = error.message;
  });
