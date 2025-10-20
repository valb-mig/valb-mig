import fetch from "node-fetch";

export default async function handler(req, res) {
  const username = "valb-mig"; // pode receber via req.query.user

  const headers = {
    "User-Agent": "ascii-profile",
    "Accept": "application/vnd.github+json"
  };

  // 1️⃣ Pegar repositórios
  const reposRes = await fetch(`https://api.github.com/users/${username}/repos?per_page=100`, { headers });
  const repos = await reposRes.json();

  // Linguagens e estrelas
  const languageBytes = {};
  let stars = 0;
  for (const repo of repos) {
    stars += repo.stargazers_count;
    if (repo.language) {
      languageBytes[repo.language] = (languageBytes[repo.language] || 0) + 1;
    }
  }

  const topLangs = Object.entries(languageBytes)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([lang]) => lang)
    .join(", ");

  // 2️⃣ Pull Requests
  const prsRes = await fetch(`https://api.github.com/search/issues?q=type:pr+author:${username}`, { headers });
  const { total_count: prs } = await prsRes.json();

  // 3️⃣ Issues
  const issuesRes = await fetch(`https://api.github.com/search/issues?q=type:issue+author:${username}`, { headers });
  const { total_count: issues } = await issuesRes.json();

  // 4️⃣ Commits (precisa header específico)
  const commitsRes = await fetch(
    `https://api.github.com/search/commits?q=author:${username}`,
    {
      headers: {
        ...headers,
        "Accept": "application/vnd.github.cloak-preview"
      }
    }
  );
  const { total_count: commits } = await commitsRes.json();

  // 5️⃣ ASCII final 😎
  const ascii = [
      `╭───────────────────────────────╮`,
      `│ user        │ ${username}`,
      `│ langs       │ ${topLangs}`,
      `│ commits     │ ${commits ?? "??"}`,
      `│ stars       │ ${stars}`,
      `│ pull reqs   │ ${prs}`,
      `│ issues      │ ${issues}`,
      `╰───────────────────────────────╯`,
  ];

    const lineHeight = 18;
    const padding = 12;
    const width = 820;
    const height = padding * 2 + ascii.length * lineHeight;

    // Escape XML chars (just in case)
    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Build <tspan> per line for crisp monospace rendering
    const tspans = ascii.map((ln, i) => `<tspan x="${padding}" dy="${i === 0 ? '1em' : '1.15em'}">${esc(ln)}</tspan>`).join('');

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="100%" height="100%" fill="#0b0f14"/>
  <g font-family="Courier New, monospace" font-size="14" fill="#e6edf3">
    <text x="${padding}" y="${padding}" xml:space="preserve">
      ${tspans}
    </text>
  </g>
  <!-- small footer -->
  <text x="${width - 12}" y="${height - 6}" font-family="sans-serif" font-size="10" fill="#6b7280" text-anchor="end">
    Updated: ${new Date().toISOString().slice(0,19).replace('T',' ')}
  </text>
</svg>`;

  res.setHeader('Content-Type', 'image/svg+xml; charset=utf-8');
  res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=7200');
  res.status(200).send(svg);
}
