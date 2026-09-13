/**
 * Anime Info — Mini App
 * Optimized for fast initial load, cached state transitions,
 * non-blocking loading indicators, and clean typography.
 */

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.expand();
  if (tg.setHeaderColor) tg.setHeaderColor("#0d0e12");
  if (tg.setBackgroundColor) tg.setBackgroundColor("#0d0e12");
}

const INIT_DATA = tg?.initData || "";
const API_HEADERS = {
  "Content-Type": "application/json",
  "X-Init-Data": INIT_DATA
};

// ── IN-MEMORY CACHE & STATE ──
const state = {
  currentScreen: "home",
  previousScreen: "home",
  activeFilter: "trending",
  discoverCache: null,
  catalogCache: {},
  searchCache: {},
  detailCache: {},
  watchlistSet: new Set(),
  favoritesSet: new Set(),
  searchTimer: null
};

// ── LOADER & TOAST FEEDBACK ──
const loader = {
  start() {
    const el = document.getElementById("top-loader");
    if (el) {
      el.classList.remove("complete");
      el.classList.add("active");
    }
  },
  done() {
    const el = document.getElementById("top-loader");
    if (el) {
      el.classList.remove("active");
      el.classList.add("complete");
    }
  }
};

let toastTimeout = null;
function notify(text, duration = 2000) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = text;
  el.classList.remove("hidden");
  el.classList.add("show");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    el.classList.remove("show");
    setTimeout(() => el.classList.add("hidden"), 200);
  }, duration);
}

// ── API REQUEST HELPER ──
async function request(endpoint, options = {}) {
  loader.start();
  try {
    const res = await fetch(endpoint, { headers: API_HEADERS, ...options });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[API] ${endpoint} failed:`, err);
    throw err;
  } finally {
    loader.done();
  }
}

// ── UTILITY HELPERS ──
function cleanTitle(item) {
  return item?.title?.english || item?.title?.romaji || item?.title || "Unknown";
}

function getCover(item) {
  return item?.coverImage?.extraLarge || item?.coverImage?.large || item?.poster_image || "";
}

function stripTags(html = "") {
  return html.replace(/<[^>]+>/g, "").trim();
}

// ── NAVIGATION CONTROLLER ──
function navigateTo(screenName, saveHistory = true) {
  if (saveHistory) state.previousScreen = state.currentScreen;
  state.currentScreen = screenName;

  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  const target = document.getElementById(`screen-${screenName}`);
  if (target) target.classList.add("active");

  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.screen === screenName);
  });

  window.scrollTo({ top: 0, behavior: "instant" });
}

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    const screen = btn.dataset.screen;
    if (screen === "catalog") {
      navigateTo("catalog");
      loadCatalog(state.activeFilter);
    } else {
      navigateTo("home");
    }
  });
});

document.getElementById("back-btn")?.addEventListener("click", () => {
  navigateTo(state.previousScreen || "home", false);
});

// ── CARD COMPONENT ──
function createCard(item, isGrid = false) {
  const id = item.id || item.anime_id;
  const title = cleanTitle(item);
  const cover = getCover(item);
  const score = item.averageScore ? (item.averageScore / 10).toFixed(1) : null;
  const progress = item.progress;

  const card = document.createElement("div");
  card.className = "card-item";
  card.innerHTML = `
    ${cover ? `<img src="${cover}" alt="${title}" loading="lazy">` : `<div style="height:160px;background:#15171e"></div>`}
    ${score ? `<span class="card-score">★ ${score}</span>` : ""}
    ${progress !== undefined ? `<span class="card-badge">Ep ${progress}</span>` : ""}
    <div class="card-title">${title}</div>
  `;

  card.addEventListener("click", () => openDetail(id, item));
  return card;
}

// ── DISCOVER SCREEN ──
async function loadDiscover(forceRefresh = false) {
  // Check local cache first for instant render
  if (!forceRefresh && state.discoverCache) {
    renderDiscover(state.discoverCache);
    return;
  }

  // Check sessionStorage for fast start
  try {
    const cached = sessionStorage.getItem("cache_discover");
    if (!forceRefresh && cached) {
      state.discoverCache = JSON.parse(cached);
      renderDiscover(state.discoverCache);
    }
  } catch (e) {}

  try {
    const data = await request("/api/discover");
    state.discoverCache = data;
    try { sessionStorage.setItem("cache_discover", JSON.stringify(data)); } catch (e) {}

    // Hydrate user watchlist set
    if (data.watchlist) {
      state.watchlistSet = new Set(data.watchlist.map(w => w.anime_id));
    }

    renderDiscover(data);
  } catch (err) {
    if (!state.discoverCache) {
      document.getElementById("carousel").innerHTML = `<p class="status-msg">Unable to load titles right now.</p>`;
    }
  }
}

function renderDiscover(data) {
  const user = data.user;
  const greetEl = document.getElementById("user-greeting");
  if (greetEl && user?.first_name) {
    greetEl.textContent = `Welcome, ${user.first_name}`;
  }

  // Render carousel
  const carousel = document.getElementById("carousel");
  if (carousel && data.carousel) {
    carousel.innerHTML = "";
    data.carousel.forEach(item => carousel.appendChild(createCard(item)));
    if (!data.carousel.length) {
      carousel.innerHTML = `<p class="status-msg">No trending titles available.</p>`;
    }
  }

  // Render watchlist preview
  const wlEl = document.getElementById("watchlist-home");
  const countEl = document.getElementById("watchlist-count");
  if (wlEl) {
    const list = data.watchlist || [];
    if (countEl) countEl.textContent = list.length ? `${list.length} saved` : "";
    wlEl.innerHTML = "";
    if (list.length) {
      list.forEach(item => wlEl.appendChild(createCard(item, true)));
    } else {
      wlEl.innerHTML = `<p class="status-msg">Your watchlist is empty.</p>`;
    }
  }
}

// ── SEARCH CONTROLLER ──
const searchInput = document.getElementById("search-input");
const searchClear = document.getElementById("search-clear");
const searchWrap = document.getElementById("search-results-wrap");
const searchResults = document.getElementById("search-results");
const searchCount = document.getElementById("search-count");
const homeContent = document.getElementById("home-content");

if (searchInput) {
  searchInput.addEventListener("input", (e) => {
    const q = e.target.value.trim();
    if (searchClear) searchClear.classList.toggle("hidden", !q);

    clearTimeout(state.searchTimer);
    if (!q) {
      searchWrap.classList.add("hidden");
      homeContent.classList.remove("hidden");
      return;
    }

    state.searchTimer = setTimeout(() => executeSearch(q), 300);
  });
}

if (searchClear) {
  searchClear.addEventListener("click", () => {
    if (searchInput) searchInput.value = "";
    searchClear.classList.add("hidden");
    searchWrap.classList.add("hidden");
    homeContent.classList.remove("hidden");
  });
}

async function executeSearch(query) {
  searchWrap.classList.remove("hidden");
  homeContent.classList.add("hidden");

  if (state.searchCache[query]) {
    renderSearchResults(state.searchCache[query]);
    return;
  }

  searchResults.innerHTML = `<div class="loading-state" style="grid-column:1/-1"><div class="spinner-ring"></div><span>Searching...</span></div>`;

  try {
    const data = await request(`/api/search?q=${encodeURIComponent(query)}`);
    const results = data.results || [];
    state.searchCache[query] = results;
    renderSearchResults(results);
  } catch (err) {
    searchResults.innerHTML = `<p class="status-msg">Search request failed.</p>`;
  }
}

function renderSearchResults(results) {
  if (searchCount) searchCount.textContent = `${results.length} found`;
  searchResults.innerHTML = "";
  if (results.length) {
    results.forEach(item => searchResults.appendChild(createCard(item, true)));
  } else {
    searchResults.innerHTML = `<p class="status-msg">No results matching that title.</p>`;
  }
}

// ── CATALOG SCREEN ──
document.querySelectorAll(".filter-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    state.activeFilter = chip.dataset.filter;
    loadCatalog(state.activeFilter);
  });
});

async function loadCatalog(filter = "trending") {
  const container = document.getElementById("catalog-content");

  // Instant render from cache if available
  if (state.catalogCache[filter]) {
    renderCatalog(state.catalogCache[filter]);
    return;
  }

  container.innerHTML = `
    <div class="loading-state">
      <div class="spinner-ring"></div>
      <span>Loading catalog...</span>
    </div>
  `;

  try {
    const data = await request(`/api/catalog?filter=${filter}`);
    const catalog = data.catalog || {};
    state.catalogCache[filter] = catalog;
    renderCatalog(catalog);
  } catch (err) {
    container.innerHTML = `<p class="status-msg" style="padding:16px">Failed to load catalog.</p>`;
  }
}

function renderCatalog(grouped) {
  const container = document.getElementById("catalog-content");
  container.innerHTML = "";

  const letters = Object.keys(grouped).sort();
  if (!letters.length) {
    container.innerHTML = `<p class="status-msg" style="padding:16px">No titles available in this category.</p>`;
    return;
  }

  letters.forEach(letter => {
    const header = document.createElement("div");
    header.className = "letter-divider";
    header.textContent = `— ${letter}`;
    container.appendChild(header);

    const grid = document.createElement("div");
    grid.className = "grid-layout";
    grouped[letter].forEach(item => grid.appendChild(createCard(item, true)));
    container.appendChild(grid);
  });
}

// ── DETAIL SCREEN ──
async function openDetail(animeId, preliminaryData = null) {
  navigateTo("detail");
  const container = document.getElementById("detail-content");

  // Immediate layout render using available metadata
  if (preliminaryData) {
    renderDetailView(preliminaryData, false);
  } else {
    container.innerHTML = `
      <div class="loading-state" style="padding-top:60px">
        <div class="spinner-ring"></div>
        <span>Loading details...</span>
      </div>
    `;
  }

  // Hydrate full data from API or memory
  if (state.detailCache[animeId]) {
    renderDetailView(state.detailCache[animeId], true);
    return;
  }

  try {
    const fullData = await request(`/api/anime/${animeId}`);
    state.detailCache[animeId] = fullData;
    renderDetailView(fullData, true);
  } catch (err) {
    if (!preliminaryData) {
      container.innerHTML = `<p class="status-msg" style="padding:24px">Unable to retrieve anime details.</p>`;
    }
  }
}

function renderDetailView(item, isHydrated = true) {
  const container = document.getElementById("detail-content");
  const id = item.id || item.anime_id;
  const title = cleanTitle(item);
  const cover = getCover(item);
  const banner = item.bannerImage || cover;
  const score = item.averageScore ? `${(item.averageScore / 10).toFixed(1)} / 10` : "Unrated";
  const status = item.status || "Unknown";
  const eps = item.episodes ? `${item.episodes} Episodes` : "Ongoing";
  const genres = (item.genres || []).map(g => `<span class="tag-item">${g}</span>`).join("");
  const description = stripTags(item.description || "No synopsis available.");
  
  const inWatchlist = item.in_watchlist !== undefined ? item.in_watchlist : state.watchlistSet.has(id);
  const isFavorite = item.is_favorite !== undefined ? item.is_favorite : state.favoritesSet.has(id);
  const progress = item.progress || 0;

  // Sync quick fav button in top nav
  const quickFav = document.getElementById("detail-fav-quick");
  if (quickFav) {
    quickFav.textContent = isFavorite ? "★" : "☆";
    quickFav.classList.toggle("is-fav", isFavorite);
    quickFav.onclick = () => toggleFavAction(id, title, cover);
  }

  container.innerHTML = `
    ${banner ? `<img class="detail-banner-img" src="${banner}" alt="${title}" loading="lazy">` : ""}

    <div class="detail-header-block">
      ${cover ? `<img class="detail-poster-img" src="${cover}" alt="${title}">` : ""}
      <div class="detail-meta-block">
        <h2 class="detail-name">${title}</h2>
        <div class="detail-stat">Score: <span>★ ${score}</span></div>
        <div class="detail-stat">Status: <span>${status}</span></div>
        <div class="detail-stat">Length: <span>${eps}</span></div>
      </div>
    </div>

    ${genres ? `<div class="tag-cloud">${genres}</div>` : ""}

    <p class="detail-summary collapsed" id="summary-text">${description}</p>
    <button class="expand-toggle" id="summary-toggle">Show more ›</button>

    <div class="action-grid">
      <button class="btn-primary ${inWatchlist ? "in-list" : ""}" id="btn-watchlist-toggle">
        ${inWatchlist ? "✓ In Watchlist" : "+ Add to Watchlist"}
      </button>
      <button class="btn-secondary ${isFavorite ? "is-fav" : ""}" id="btn-fav-toggle">
        ${isFavorite ? "★ Favorited" : "☆ Favorite"}
      </button>

      ${inWatchlist ? `
        <button class="btn-accent" id="btn-inc-progress">
          +1 Episode Progress (Ep ${progress})
        </button>
      ` : ""}

      ${item.siteUrl ? `
        <a class="btn-link" href="${item.siteUrl}" target="_blank">
          View Profile on AniList ›
        </a>
      ` : ""}
    </div>
  `;

  // Synopsis expansion
  const toggleBtn = document.getElementById("summary-toggle");
  const summaryEl = document.getElementById("summary-text");
  if (toggleBtn && summaryEl) {
    toggleBtn.addEventListener("click", () => {
      const isCollapsed = summaryEl.classList.toggle("collapsed");
      toggleBtn.textContent = isCollapsed ? "Show more ›" : "Show less ‹";
    });
  }

  // Watchlist action handler
  const wlBtn = document.getElementById("btn-watchlist-toggle");
  if (wlBtn) {
    wlBtn.addEventListener("click", async () => {
      const currentlyIn = wlBtn.classList.contains("in-list");
      if (currentlyIn) {
        // Optimistic UI
        wlBtn.classList.remove("in-list");
        wlBtn.textContent = "+ Add to Watchlist";
        state.watchlistSet.delete(id);
        notify("Removed from watchlist.");
        document.getElementById("btn-inc-progress")?.remove();
        
        await request(`/api/watchlist/${id}`, { method: "DELETE" }).catch(() => {});
      } else {
        wlBtn.classList.add("in-list");
        wlBtn.textContent = "✓ In Watchlist";
        state.watchlistSet.add(id);
        notify("Added to watchlist.");

        await request("/api/watchlist", {
          method: "POST",
          body: JSON.stringify({
            anime_id: id,
            title: title,
            poster_image: cover,
            total_episodes: item.episodes || 0
          })
        }).catch(() => {});
      }
      // Invalidate discover cache to refresh next visit
      state.discoverCache = null;
    });
  }

  // Favorite toggle action
  const favBtn = document.getElementById("btn-fav-toggle");
  if (favBtn) {
    favBtn.addEventListener("click", () => toggleFavAction(id, title, cover));
  }

  // Increment episode progress
  const progBtn = document.getElementById("btn-inc-progress");
  if (progBtn) {
    progBtn.addEventListener("click", async () => {
      try {
        const res = await request(`/api/watchlist/${id}/progress`, { method: "PATCH" });
        const newProgress = res.progress ?? (progress + 1);
        progBtn.textContent = `+1 Episode Progress (Ep ${newProgress})`;
        notify(`Progress updated: Episode ${newProgress}`);
        state.discoverCache = null;
      } catch (e) {
        notify("Failed to update progress.");
      }
    });
  }
}

async function toggleFavAction(id, title, cover) {
  const favBtn = document.getElementById("btn-fav-toggle");
  const quickFav = document.getElementById("detail-fav-quick");

  try {
    const res = await request("/api/favorites/toggle", {
      method: "POST",
      body: JSON.stringify({ anime_id: id, title: title, poster_image: cover })
    });

    const isFav = res.is_favorite;
    if (isFav) {
      state.favoritesSet.add(id);
      notify("Saved to favorites.");
    } else {
      state.favoritesSet.delete(id);
      notify("Removed from favorites.");
    }

    if (favBtn) {
      favBtn.classList.toggle("is-fav", isFav);
      favBtn.textContent = isFav ? "★ Favorited" : "☆ Favorite";
    }
    if (quickFav) {
      quickFav.classList.toggle("is-fav", isFav);
      quickFav.textContent = isFav ? "★" : "☆";
    }
  } catch (e) {
    notify("Could not update favorites.");
  }
}

// ── INITIALIZATION ──
document.addEventListener("DOMContentLoaded", () => {
  loadDiscover();
});
