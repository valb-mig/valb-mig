import fetch from "node-fetch";

export default async function handler(req, res) {
  const username = req.query.user || "valb-mig";

  const headers = {
    "User-Agent": "ascii-profile",
    "Accept": "application/vnd.github+json"
  };

  // Coleta dados do GitHub
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

  const prsRes = await fetch(`https://api.github.com/search/issues?q=type:pr+author:${username}`, { headers });
  const { total_count: prs } = await prsRes.json();

  const issuesRes = await fetch(`https://api.github.com/search/issues?q=type:issue+author:${username}`, { headers });
  const { total_count: issues } = await issuesRes.json();

  const commitsRes = await fetch(`https://api.github.com/search/commits?q=author:${username}`, {
    headers: {
      ...headers,
      "Accept": "application/vnd.github.cloak-preview"
    }
  });
  const { total_count: commits } = await commitsRes.json();

  // --- SVG pequeno (dinâmico) ---
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

  const tspans = ascii
    .map((ln, i) => `<tspan x="16" dy="${i === 0 ? '1.5em' : '1.2em'}">${ln}</tspan>`)
    .join('');

  const innerSvg = `
  <svg xmlns="http://www.w3.org/2000/svg" width="460" height="460" viewBox="0 0 460 460">
    <rect width="460" height="260" rx="10" ry="10" fill="#000000de"/>
    <rect width="460" height="32" rx="10" ry="10" fill="#000000ff"/>
    <circle cx="20" cy="16" r="6" fill="#ff5f56"/>
    <circle cx="40" cy="16" r="6" fill="#ffbd2e"/>
    <circle cx="60" cy="16" r="6" fill="#27c93f"/>
    <text x="230" y="21" font-family="sans-serif" font-size="13" fill="#ffffffff" text-anchor="middle">~/github-status</text>
    <text x="16" y="55" fill="#79c0ff">valb@system ➜ ~ </text>
    <text x="16" y="70" font-family="Courier New, monospace" font-size="14" fill="#e6edf3">${tspans}</text>
  </svg>`;

  // --- SVG grande (pai) ---
  const fullSvg = `
  <svg xmlns="http://www.w3.org/2000/svg" width="860" height="760" viewBox="0 0 960 760">
    <svg width="820" height="502" viewBox="0 0 820 502">
      <style>
        text {
          font-family: 'Courier New', monospace;
          font-size: 14px;
          fill: #e6edf3;
          white-space: pre;
        }
      </style>
      <rect x="0" y="0" width="820" height="502" rx="10" ry="10" fill="#000000de"/>
      <rect x="0" y="0" width="820" height="32" rx="10" ry="10" fill="#000000ff"/>
      <circle cx="20" cy="16" r="6" fill="#ff5f56"/>
      <circle cx="40" cy="16" r="6" fill="#ffbd2e"/>
      <circle cx="60" cy="16" r="6" fill="#27c93f"/>
      <text x="410" y="21" font-family="sans-serif" font-size="13" fill="#ffffffff" text-anchor="middle">~/</text>
      <text x="16" y="70">
      <tspan x="16" dy="1.5em"> ######   #    ########## #         #       ######   </tspan><tspan x="16" dy="1.2em">           #          ###  #    ##########            </tspan><tspan x="16" dy="1.2em">########## ##        #     ##        #     ########## </tspan><tspan x="16" dy="1.2em">     #     # #      #      # #       #          #     </tspan><tspan x="16" dy="1.2em">     #     #  #    #       #  #     #           #     </tspan><tspan x="16" dy="1.2em">    #      #      #        #       #           #      </tspan><tspan x="16" dy="1.2em">  ##       #     #         #     ##          ##       </tspan><tspan x="16" dy="1.2em">                                                   </tspan><tspan x="16" dy="1.2em">     </tspan><tspan x="16" dy="1.2em">valb@system ➜ ~ cat ~/profile.txt</tspan><tspan x="16" dy="1.2em">     </tspan><tspan x="16" dy="1.2em">╭──────────╮</tspan><tspan x="16" dy="1.2em">│ user     │  valb</tspan><tspan x="16" dy="1.2em">│ hname    │  Ivalber Miguel</tspan><tspan x="16" dy="1.2em">│ uptime   │  21 Years</tspan><tspan x="16" dy="1.2em">│ lang     │  PHP, Typescript, Kotlin</tspan><tspan x="16" dy="1.2em">│ process  │  code(); lift(); cook(); repeat();</tspan><tspan x="16" dy="1.2em">│ location │  8° 04' 03"S lat e 34° 55' 00"W lng</tspan><tspan x="16" dy="1.2em">├──────────┤</tspan><tspan x="16" dy="1.2em">│ pin      │  /home/valb/Projects/php.rpg-playground</tspan><tspan x="16" dy="1.2em">╰──────────╯</tspan><tspan x="16" dy="1.2em">     </tspan><tspan x="16" dy="1.2em">valb@system ➜ ~ </tspan>
      </text>
      <!-- Aqui o mini-terminal -->
      <g transform="translate(480,0)">
        ${innerSvg}
      </g>
    </svg>
  </svg>`;

  res.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
  res.setHeader("Cache-Control", "s-maxage=3600, stale-while-revalidate=7200");
  res.status(200).send(fullSvg);
}
