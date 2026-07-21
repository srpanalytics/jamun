/* Thin wrapper around fetch() for JSON APIs. */
const Api = {
  async get(url) {
    const res = await fetch(url, { headers: { "Accept": "application/json" } });
    return Api._handle(res);
  },
  async post(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(body || {}),
    });
    return Api._handle(res);
  },
  async _handle(res) {
    let data = null;
    try { data = await res.json(); } catch (e) { /* no body */ }
    if (!res.ok) {
      const message = (data && data.error) || `Request failed (${res.status})`;
      throw new Error(message);
    }
    return data;
  },
};
