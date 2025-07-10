const grid = document.getElementById("cardGrid"), api = "/events";

async function fetchEvents() { return (await fetch(api)).json(); }
async function deleteEvent(id) { await fetch(`${api}/${id}`, { method: "DELETE" }); }

function pad(n) { return String(n).padStart(2, "0"); }
function diff(ms) { const d = Math.max(0, ms - Date.now()) / 1000; return { days: Math.floor(d / 86400), hours: Math.floor(d % 86400 / 3600), minutes: Math.floor(d % 3600 / 60), seconds: Math.floor(d % 60) }; }
function fmtDate(ds) { return new Date(ds).toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }); }

function renderCard(ev) {
    const c = document.createElement("div");
    c.className = "card shadow-sm border-0 text-center";
    c.dataset.date = ev.date; c.dataset.id = ev.id;
    c.innerHTML = `
  <div class="bg-primary text-white py-2 d-flex justify-content-between align-items-center px-3 rounded-top">
    <h5 class="mb-0 flex-grow-1 text-truncate">${ev.title}</h5>
    <button class="btn btn-sm btn-light text-danger fw-semibold flex-shrink-0" data-action="del">✕</button>
  </div>
  <div class="card-body">
    <p class="text-muted small mb-4">${fmtDate(ev.date)}</p>
    <div class="d-flex justify-content-center align-items-center gap-4 flex-wrap">
      <div><div class="time-num" data-u="days">00</div><div class="text-secondary small">Tage</div></div>
      <div class="fs-4">:</div>
      <div><div class="time-num" data-u="hours">00</div><div class="text-secondary small">Stunden</div></div>
      <div class="fs-4">:</div>
      <div><div class="time-num" data-u="minutes">00</div><div class="text-secondary small">Minuten</div></div>
      <div class="fs-4">:</div>
      <div><div class="time-num" data-u="seconds">00</div><div class="text-secondary small">Sekunden</div></div>
    </div>
  </div>`;
    return c;
}

function updateCard(c) {
    const t = new Date(c.dataset.date).getTime(), { days: d, hours: h, minutes: m, seconds: s } = diff(t), red = t - Date.now() < 86400000, f = cls => `time-num fw-semibold fs-4 ${red ? "text-danger" : "text-dark"}`;
    c.querySelector('[data-u="days"]').textContent = pad(d); c.querySelector('[data-u="days"]').className = f();
    c.querySelector('[data-u="hours"]').textContent = pad(h); c.querySelector('[data-u="hours"]').className = f();
    c.querySelector('[data-u="minutes"]').textContent = pad(m); c.querySelector('[data-u="minutes"]').className = f();
    c.querySelector('[data-u="seconds"]').textContent = pad(s); c.querySelector('[data-u="seconds"]').className = f();
}

async function load() { grid.innerHTML = ""; (await fetchEvents()).forEach(ev => grid.appendChild(renderCard(ev))); }

grid.addEventListener("click", async e => { if (e.target.dataset.action === "del") { await deleteEvent(e.target.closest(".card").dataset.id); load(); } });

document.getElementById("addForm").addEventListener("submit", async e => {
    e.preventDefault();
    const dateStr = document.getElementById("date").value;                     // 1) lokale Eingabe
    const isoUtc = new Date(dateStr).toISOString();                             // 2) nach UTC-ISO
    await fetch(api, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
            title: document.getElementById("title").value,
            date: isoUtc,                                                          // 3) ISO mitschicken
            email: document.getElementById("email").value
        })
    });
    e.target.reset(); load();
});

load();
setInterval(() => grid.querySelectorAll(".card").forEach(updateCard), 1e3);
setInterval(load, 6e5);
