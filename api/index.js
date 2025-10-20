import fetch from "node-fetch";

export default async function handler(req, res) {
  const username = "valb-mig"; // pode trocar pra req.query.user

  const headers = {
    "User-Agent": "ascii-profile",
    "Accept": "application/vnd.github+json"
  };

  // 1️⃣ Pegar repositórios
  const reposRes = await fetch(`https://api.github.com/users/${username}/repos?per_page=100`, { headers });
  const repos = await reposRes.json();

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

  // 4️⃣ Commits
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
  const padding = 16;
  const width = 820;
  const height = padding * 3 + ascii.length * lineHeight + 40;

  const esc = (s) => String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const tspans = ascii
    .map((ln, i) => `<tspan x="${padding}" dy="${i === 0 ? '1.5em' : '1.2em'}">${esc(ln)}</tspan>`)
    .join('');

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <style>
    text {
      font-family: 'Courier New', monospace;
      font-size: 14px;
      fill: #e6edf3;
      white-space: pre;
    }
  </style>

  <!-- Terminal window background -->
  <rect x="0" y="0" width="${width}" height="${height}" rx="10" ry="10" fill="#0D1117"/>

  <!-- Title bar -->
  <rect x="0" y="0" width="${width}" height="32" rx="10" ry="10" fill="#161b22"/>

  <!-- Buttons -->
  <circle cx="20" cy="16" r="6" fill="#ff5f56"/>
  <circle cx="40" cy="16" r="6" fill="#ffbd2e"/>
  <circle cx="60" cy="16" r="6" fill="#27c93f"/>

  <!-- Title text -->
  <text x="${width / 2}" y="21" font-family="sans-serif" font-size="13" fill="#8b949e" text-anchor="middle">~/github-status</text>

  <!-- Command line -->
  <text x="${padding}" y="55" font-family="Courier New, monospace" font-size="14" fill="#79c0ff">$ ./github-status</text>

  <!-- ASCII output -->
  <text x="${padding}" y="70">
    ${tspans}
  </text>
</svg>`;

  res.setHeader('Content-Type', 'image/svg+xml; charset=utf-8');
  res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=7200');
  res.status(200).send(svg);
}
