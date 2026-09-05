/* 把整個 App 和字典資料存到裝置上，之後完全不連網也能用。 */
const VERSION = "c9ac4f7ba22b";
const CACHE = "pinyin-dict-" + VERSION;

const ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.webmanifest",
  "./icons/icon-180.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./data/meta.json",
  "./data/chars.txt",
  "./data/words.txt",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(names.filter((n) => n.startsWith("pinyin-dict-") && n !== CACHE).map((n) => caches.delete(n)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;

  event.respondWith(
    caches.match(request).then((hit) => {
      if (hit) return hit;
      return fetch(request).catch(() => {
        // 離線又沒快取到：導覽請求一律回首頁，其餘就讓它失敗。
        if (request.mode === "navigate") return caches.match("./index.html");
        return Response.error();
      });
    })
  );
});
