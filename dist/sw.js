/*Service worker de U24. 
Cachea la app completa en la instalación para que buscar funcione sin cobertura.
Estrategia: cache-first para lo propio; la red solo se usa para actualizar.*/

const CACHE = 'u24-91f05aa7eb58';
const DOC = './index.html';

/*Cuánto se espera a la red antes de servir la copia guardada.
El escenario real del operativo no es «sin red», es «red saturada»: ahí un fetch no falla, se queda esperando el tiempo que decida el navegador, que pueden ser decenas de segundos. 
Sin este límite, la app que debe abrirse en menos de un segundo tardaba justo cuando más falta hace.
La red sigue teniendo preferencia mientras responda a tiempo, para que una corrección de coordenadas llegue en la misma apertura y no en la siguiente.*/
const NETWORK_TIMEOUT = 1500;

/*Solo lo imprescindible para que la app funcione sin cobertura.
 index.html ya lleva dentro los datos, el motor de búsqueda, la tipografía y el emblema. 
 Los iconos NO se precachean: los descarga el sistema al instalar el acceso directo y no hacen falta para buscar. 
 Precacharlos costaba 680 KB extra antes de que la app estuviera lista, justo donde la red está saturada. 
 El manejador de fetch los cachea igualmente si el navegador los pide.*/
const ASSETS = [
  './',
  DOC,
  './manifest.webmanifest'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      // addAll falla en bloque si un recurso no existe: se añaden de uno en uno.
      .then(cache => Promise.all(
        ASSETS.map(url => cache.add(url).catch(() => {}))
      ))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

/**Pide el documento a la red y guarda la copia nueva para la próxima vez.*/
function fetchDocument(req){
  return fetch(req).then(res => {
    if (res && res.ok){
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(DOC, copy));
    }
    return res;
  });
}

/**Navegación: la red gana si contesta dentro del plazo; si no, se sirve la copia guardada y la descarga sigue en segundo plano para que la próxima apertura ya tenga lo nuevo.*/
async function navigate(event){
  const network = fetchDocument(event.request);
  const cached = await caches.match(DOC);

  // Sin copia guardada no hay alternativa que esperar a la red.
  if (!cached) return network;

  const fresh = await Promise.race([
    network.catch(() => null),
    new Promise(resolve => setTimeout(() => resolve(null), NETWORK_TIMEOUT))
  ]);
  if (fresh) return fresh;

  // La red ha llegado tarde: que termine igualmente y actualice la caché.
  event.waitUntil(network.catch(() => {}));
  return cached;
}

self.addEventListener('fetch', event => {
  const req = event.request;

  // Solo se gestionan navegaciones y recursos propios en GET.
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // El propio service worker nunca se cachea: una copia rancia aquí podría
  // impedir que el equipo reciba una corrección de coordenadas.
  if (url.pathname.endsWith('/sw.js')) return;

  if (req.mode === 'navigate'){
    event.respondWith(navigate(event));
    return;
  }

  event.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(req, copy));
      return res;
    }))
  );
});
