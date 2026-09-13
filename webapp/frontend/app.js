/* ─────────────────────────────────────────
   Anime Info Bot — Mini App
   Fully interactive: search, detail, watchlist,
   favorites, tracker, catalog with alpha groups.
───────────────────────────────────────── */

const tg = window.Telegram?.WebApp;
if (tg) tg.expand();

const INIT_DATA = tg?.initData || "";
const headers = { "Content-Type": "application/json", "X-Init-Data": INIT_DATA };

// ── STATE ──
let currentScreen = "home";
let previousScreen = "home";
let currentDetail = null;
let searchTimer = null;

// ── UTILS ──
function toast(msg, duration = 2200) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  el.classList.add("show");
  setTimeout(() => {
    el.classList.remove("show");
    setTimeout(() => el.classList.add("hidden"), 300);
  }, duration);
}

function api(path, opts = {}) {
  return fetch(path, { headers, ...opts }).then(r => r.json());
}

function getTitle(item) {
  return item?.title?.english || item?.title?.romaji || item?.title || "Unknown";
}

function getPoster(item) {
  return item?.coverImage?.extraLarge || item?.coverImage?.large || item?.poster_image || "";
}

function cleanHtml(str = "") {
  return str.replace(/<[^>]+>/g, "").trim();
}

// ── NAVIGATION ──
function showScreen(name, push = true) {
  if (push) previousScreen = currentScreen;
  currentScreen = name;
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(`screen-${name}`).classList.add("active");
  document.querySelectorAll(".nav-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.screen === name);
  });
}

document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.screen;
    if (target === "catalog" && currentScreen !== "catalog") {
      showScreen("catalog");
      loadCatalog("trending");
    } else {
      showScreen(target);
    }
  });
});

document.getElementById("back-btn").addEventListener("click", () => {
  showScreen(previousScreen, false);
});

// ── POSTER CARD ──
function makePosterCard(item, size = "carousel") {
  const title = getTitle(item);
  const poster = getPoster(item);
  const score = item.averageScore ? `⭐ ${(item.averageScore / 10).toFixed(1)}` : "";
  const id = item.id || item.anime_id;

  const card = document.createElement("div");
  card.className = size === "grid" ? "grid-card" : "poster-card";
  card.innerHTML = `
    ${poster ? `<img src="${poster}" alt="${title}" loading="lazy">` : `<div style="height:180px;background:#1a1a22"></div>`}
    ${score ? `<span class="card-score">${score}</span>` : ""}
    <div class="card-title">${title}</div>
    ${item.progress !== undefined ? `<span class="progress-badge">Ep ${item.progress}</span>` : ""}
  `;
  card.addEventListener("click", () => openDetail(id, item));
  return card;
}

// ── SEARCH ──
document.getElementById("search-input").addEventListener("input", e => {
  clearTimeout(searchTimer);
  const q = e.target.value.trim();
  searchTimer = setTimeout(() => runSearch(q), 350);
});

async function runSearch(q) {
  const wrap = document.getElementById("search-results-wrap");
  const home = document.getElementById("home-content");
  const resultsEl = document.getElementById("search-results");

  if (!q) {
    wrap.classList.add("hidden");
    home.classList.remove("hidden");
    return;
  }

  wrap.classList.remove("hidden");
  home.classList.add("hidden");
  resultsEl.innerHTML = `<p class="empty-msg" style="grid-column:1/-1">Searching...</p>`;

  const data = await api(`/api/search?q=${encodeURIComponent(q)}`);
  const items = data.results || [];

  if (!items.length) {
    resultsEl.innerHTML = `<p class="empty-msg">No results found.</p>`;
    return;
  }

  resultsEl.innerHTML = "";
  items.forEach(item => resultsEl.appendChild(makePosterCard(item, "grid")));
}

// ── HOME ──
async function loadHome() {
  const data = await api("/api/discover");

  // Greeting
  const user = data.user;
  const greetEl = document.getElementById("user-greeting");
  if (user?.first_name) greetEl.textContent = `Hi, ${user.first_name} 👋`;

  // Carousel
  const carousel = document.getElementById("carousel");
  carousel.innerHTML = "";
  (data.carousel || []).forEach(item => carousel.appendChild(makePosterCard(item, "carousel")));
  if (!data.carousel?.length) carousel.innerHTML = `<p class="empty-msg">Nothing trending right now.</p>`;

  // Watchlist on home
  const wlEl = document.getElementById("watchlist-home");
  wlEl.innerHTML = "";
  const wl = data.watchlist || [];
  if (!wl.length) {
    wlEl.innerHTML = `<p class="empty-msg">Nothing here yet — add anime to your watchlist!</p>`;
  } else {
    wl.forEach(item => wlEl.appendChild(makePosterCard(item, "grid")));
  }
}

// ── CATALOG ──
let activeCatalogFilter = "trending";

document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    activeCatalogFilter = chip.dataset.filter;
    loadCatalog(activeCatalogFilter);
  });
});

async function loadCatalog(filter = "trending") {
  const el = document.getElementById("catalog-content");
  el.innerHTML = `<div class="loading-spinner">⏳ Loading...</div>`;
  const data = await api(`/api/catalog?filter=${filter}`);
  const grouped = data.catalog || {};

  el.innerHTML = "";
  const letters = Object.keys(grouped).sort();
  if (!letters.length) {
    el.innerHTML = `<p class="empty-msg" style="padding:16px">No titles found.</p>`;
    return;
  }

  letters.forEach(letter => {
    const header = document.createElement("div");
    header.className = "letter-header";
    header.textContent = letter;
    el.appendChild(header);

    const grid = document.createElement("div");
    grid.className = "grid-3";
    grouped[letter].forEach(item => grid.appendChild(makePosterCard(item, "grid")));
    el.appendChild(grid);
  });
}

// ── DETAIL ──
async function openDetail(animeId, cachedItem = null) {
  showScreen("detail");
  const el = document.getElementById("detail-content");
  el.innerHTML = `<div class="loading-spinner" style="padding-top:60px">⏳ Loading...</div>`;

  let item;
  try {
    item = await api(`/api/anime/${animeId}`);
  } catch (e) {
    // Fallback to cached data if API fails
    item = cachedItem || {};
  }

  currentDetail = item;
  const title = getTitle(item);
  const poster = getPoster(item);
  const banner = item.bannerImage || poster;
  const score = item.averageScore ? `⭐ ${(item.averageScore / 10).toFixed(1)}/10` : "N/A";
  const status = item.status || "Unknown";
  const episodes = item.episodes ? `${item.episodes} eps` : "Ongoing";
  const genres = (item.genres || []).map(g => `<span class="genre-tag">${g}</span>`).join("");
  const synopsis = cleanHtml(item.description || "No synopsis available.");
  const inWl = item.in_watchlist || false;
  const isFav = item.is_favorite || false;
  const progress = item.progress || 0;

  el.innerHTML = `
    ${banner ? `<img class="detail-banner" src="${banner}" alt="${title}" loading="lazy">` : ""}

    <div class="detail-poster-wrap">
      ${poster ? `<img class="detail-poster" src="${poster}" alt="${title}">` : ""}
      <div class="detail-meta">
        <div class="detail-title">${title}</div>
        <div class="detail-score">${score}</div>
        <div class="detail-status">${status}</div>
        <div class="detail-episodes">${episodes}</div>
      </div>
    </div>

    ${genres ? `<div class="detail-genres">${genres}</div>` : ""}

    <p class="detail-synopsis collapsed" id="synopsis-text">${synopsis}</p>
    <button class="read-more-btn" id="read-more-btn">Read more ▼</button>

    <div class="action-row">
      <button class="action-btn btn-watchlist ${inWl ? "in-wl" : ""}" id="btn-wl">
        ${inWl ? "✓ In Watchlist" : "＋ Watchlist"}
      </button>
      <button class="action-btn btn-favorite ${isFav ? "is-fav" : ""}" id="btn-fav">
        ${isFav ? "★ Favorited" : "☆ Favorite"}
      </button>
    </div>

    ${inWl ? `
    <div class="action-row" style="padding-top:0">
      <button class="action-btn btn-progress" id="btn-progress">
        ＋1 Episode (Ep ${progress})
      </button>
    </div>` : ""}

    ${item.siteUrl ? `
    <div class="action-row" style="padding-top:0">
      <a href="${item.siteUrl}" target="_blank" style="text-decoration:none;flex:1">
        <button class="action-btn btn-anilist" style="width:100%">🔗 View on AniList</button>
      </a>
    </div>` : ""}
  `;

  // Read more toggle
  document.getElementById("read-more-btn")?.addEventListener("click", function() {
    const p = document.getElementById("synopsis-text");
    const collapsed = p.classList.toggle("collapsed");
    this.textContent = collapsed ? "Read more ▼" : "Read less ▲";
  });

  // Watchlist toggle
  document.getElementById("btn-wl")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-wl");
    const alreadyIn = btn.classList.contains("in-wl");

    if (alreadyIn) {
      await api(`/api/watchlist/${animeId}`, { method: "DELETE" });
      btn.classList.remove("in-wl");
      btn.textContent = "＋ Watchlist";
      toast("Removed from watchlist");
      // Hide progress button
      document.getElementById("btn-progress")?.closest(".action-row")?.remove();
    } else {
      await api("/api/watchlist", {
        method: "POST",
        body: JSON.stringify({
          anime_id: animeId,
          title: title,
          poster_image: poster,
          total_episodes: item.episodes || 0
        })
      });
      btn.classList.add("in-wl");
      btn.textContent = "✓ In Watchlist";
      toast("✅ Added to watchlist!");
    }
  });

  // Favorites toggle
  document.getElementById("btn-fav")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-fav");
    const data = await api("/api/favorites/toggle", {
      method: "POST",
      body: JSON.stringify({ anime_id: animeId, title: title, poster_image: poster })
    });
    if (data.is_favorite) {
      btn.classList.add("is-fav");
      btn.textContent = "★ Favorited";
      toast("⭐ Added to favorites!");
    } else {
      btn.classList.remove("is-fav");
      btn.textContent = "☆ Favorite";
      toast("Removed from favorites");
    }
  });

  // Progress +1
  document.getElementById("btn-progress")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-progress");
    const data = await api(`/api/watchlist/${animeId}/progress`, { method: "PATCH" });
    const newProg = data.progress ?? 0;
    btn.textContent = `＋1 Episode (Ep ${newProg})`;
    toast(`📈 Progress: Episode ${newProg}`);
  });
}

// ── INIT ──
loadHome();
