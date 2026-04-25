const CACHE = "plant-manager-v1";

// 静态资源：首次加载后缓存
const PRECACHE = [
  "/",
  "/static/style.css",
  "/static/app.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

// ── 安装：预缓存静态资源 ──────────────────────────────────────────────────────
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(PRECACHE))
  );
  self.skipWaiting();
});

// ── 激活：清理旧缓存 ──────────────────────────────────────────────────────────
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── 请求拦截策略 ──────────────────────────────────────────────────────────────
self.addEventListener("fetch", (e) => {
  const { request } = e;
  const url = new URL(request.url);

  // API / 上传文件：始终走网络，不缓存
  if (url.pathname.startsWith("/api/") ||
      url.pathname.startsWith("/uploads/") ||
      request.method !== "GET") {
    return;
  }

  // 静态资源：缓存优先
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(
      caches.match(request).then((cached) =>
        cached || fetch(request).then((res) => {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put(request, clone));
          return res;
        })
      )
    );
    return;
  }

  // 页面：网络优先，失败时返回缓存首页
  e.respondWith(
    fetch(request).catch(() => caches.match("/"))
  );
});
