module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ ok: false, error: 'Method not allowed.' });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 4000);

  try {
    const upstream = await fetch('http://40.160.137.41:4311/health', {
      cache: 'no-store',
      signal: controller.signal,
    });
    if (!upstream.ok) {
      return res.status(502).json({ ok: false, error: `OVH health returned HTTP ${upstream.status}` });
    }
    const data = await upstream.json();
    res.setHeader('Cache-Control', 'no-store');
    return res.status(200).json(data);
  } catch (error) {
    return res.status(503).json({ ok: false, error: 'OVH organism is not reachable.' });
  } finally {
    clearTimeout(timeout);
  }
};
