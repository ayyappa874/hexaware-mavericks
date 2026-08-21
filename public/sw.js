const CACHE_NAME = "survey-sentinel-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/demo",
  "/queue",
  "/observatory",
  "/models",
  "/temporal",
  "/registry",
  "/clusters"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch(() => {
        return caches.match("/");
      });
    })
  );
});
