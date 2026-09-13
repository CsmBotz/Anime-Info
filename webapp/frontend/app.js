document.addEventListener("DOMContentLoaded", () => {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.expand();
    const user = tg.initDataUnsafe?.user;
    if (user) {
      document.getElementById("user-name").textContent = user.first_name || "Anime Fan";
    }
  }

  // Navigation tab switching
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const screenId = "screen-" + tab.dataset.tab;
      document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
      document.getElementById(screenId).classList.add("active");

      if (tab.dataset.tab === "catalog") loadCatalog();
      if (tab.dataset.tab === "watchlist") loadWatchlist();
    });
  });

  // Load Discover screen on start
  loadDiscover();
});

async function loadDiscover() {
  try {
    const res = await fetch("/api/discover", {
      headers: { "X-Init-Data": window.Telegram?.WebApp?.initData || "" }
    });
    const data = await res.json();
    
    // Render Carousel
    const carouselEl = document.getElementById("trending-carousel");
    if (data.carousel && data.carousel.length) {
      carouselEl.innerHTML = data.carousel.map(item => `
        <div class="carousel-card">
          <img src="${item.coverImage?.large || ''}" alt="${item.title?.romaji || ''}">
          <div class="title">${item.title?.english || item.title?.romaji || 'Unknown'}</div>
        </div>
      `).join("");
    } else {
      carouselEl.innerHTML = "<div>No trending anime available.</div>";
    }
  } catch (e) {
    console.error("Failed to load discover page", e);
  }
}

async function loadCatalog() {
  try {
    const res = await fetch("/api/catalog", {
      headers: { "X-Init-Data": window.Telegram?.WebApp?.initData || "" }
    });
    const data = await res.json();
    const catalogEl = document.getElementById("catalog-list");

    let html = "";
    for (const [letter, items] of Object.entries(data.catalog || {})) {
      html += `<div class="letter-header">${letter}</div><div class="grid">`;
      html += items.map(item => `
        <div class="carousel-card">
          <img src="${item.coverImage?.large || ''}">
          <div class="title">${item.title?.english || item.title?.romaji || ''}</div>
        </div>
      `).join("");
      html += `</div>`;
    }
    catalogEl.innerHTML = html || "<div>Catalog is empty.</div>";
  } catch (e) {
    console.error("Failed to load catalog", e);
  }
}

async function loadWatchlist() {
  try {
    const res = await fetch("/api/watchlist", {
      headers: { "X-Init-Data": window.Telegram?.WebApp?.initData || "" }
    });
    const items = await res.json();
    const wlEl = document.getElementById("watchlist-grid");

    if (items && items.length) {
      wlEl.innerHTML = items.map(item => `
        <div class="carousel-card">
          <div class="title">${item.title}</div>
          <div style="padding: 8px; font-size:12px;">Ep: ${item.progress}/${item.total_episodes || '?'}</div>
        </div>
      `).join("");
    } else {
      wlEl.innerHTML = "<div>Your watchlist is empty!</div>";
    }
  } catch (e) {
    console.error("Failed to load watchlist", e);
  }
}

