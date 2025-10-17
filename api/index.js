export default function handler(req, res) {
  res.status(200).send("Hello World");
}


// export default async function handler(req, res) {
//   try {
//     const username = (req.url && new URL(req.url, `http://${req.headers.host}`).searchParams.get('user')) || 'valb';
//     const token = process.env.GITHUB_TOKEN || null;

//     const headersBase = {
//       'User-Agent': 'ascii-profile',
//       'Accept': 'application/vnd.github+json',
//     };
//     if (token) headersBase['Authorization'] = `Bearer ${token}`;

//     const reposRes = await fetch(`https://api.github.com/users/${username}/repos?per_page=100`, { headers: headersBase });
//     if (!reposRes.ok) {
//       const body = await reposRes.text().catch(()=>'');
//       res.status(reposRes.status).send(`Could not fetch repos: ${reposRes.status} ${body}`);
//       return;
//     }
//     const repos = await reposRes.json();

//     const langCounts = {};
//     let totalStars = 0;
//     for (const r of repos) {
//       totalStars += r.stargazers_count || 0;
//       const lang = r.language || 'Unknown';
//       langCounts[lang] = (langCounts[lang] || 0) + 1;
//     }
//     const topLangs = Object.entries(langCounts)
//       .filter(([lang]) => lang !== 'Unknown')
//       .sort((a,b) => b[1] - a[1])
//       .slice(0, 3)
//       .map(([lang, cnt]) => `${lang} (${cnt})`)
//       .join(' • ') || '—';

//     const prsRes = await fetch(`https://api.github.com/search/issues?q=type:pr+author:${username}&per_page=1`, { headers: headersBase });
//     const prsJson = prsRes.ok ? await prsRes.json() : { total_count: '??' };
//     const totalPRs = prsJson.total_count ?? '??';

//     const issuesRes = await fetch(`https://api.github.com/search/issues?q=type:issue+author:${username}&per_page=1`, { headers: headersBase });
//     const issuesJson = issuesRes.ok ? await issuesRes.json() : { total_count: '??' };
//     const totalIssues = issuesJson.total_count ?? '??';

//     const commitHeaders = { ...headersBase, Accept: 'application/vnd.github.cloak-preview' };
//     const commitsRes = await fetch(`https://api.github.com/search/commits?q=author:${username}&per_page=1`, { headers: commitHeaders });
//     const commitsJson = commitsRes.ok ? await commitsRes.json() : { total_count: '??' };
//     const totalCommits = commitsJson.total_count ?? '??';

//     const lines = [
//       `╭──────────────────────────────────────────────╮`,
//       `│ user      │ ${username.padEnd(30).slice(0,30)} │`,
//       `│ languages │ ${topLangs.padEnd(30).slice(0,30)} │`,
//       `│ commits   │ ${String(totalCommits).padEnd(30).slice(0,30)} │`,
//       `│ stars     │ ${String(totalStars).padEnd(30).slice(0,30)} │`,
//       `│ pull reqs │ ${String(totalPRs).padEnd(30).slice(0,30)} │`,
//       `│ issues    │ ${String(totalIssues).padEnd(30).slice(0,30)} │`,
//       `╰──────────────────────────────────────────────╯`
//     ];

//     const lineHeight = 18;
//     const padding = 12;
//     const width = 820;
//     const height = padding * 2 + lines.length * lineHeight;

//     const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

//     const tspans = lines.map((ln, i) => `<tspan x="${padding}" dy="${i === 0 ? '1em' : '1.15em'}">${esc(ln)}</tspan>`).join('');

//     const svg = `<?xml version="1.0" encoding="UTF-8"?>
// <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
//   <rect width="100%" height="100%" fill="#0b0f14"/>
//   <g font-family="Courier New, monospace" font-size="14" fill="#e6edf3">
//     <text x="${padding}" y="${padding}" xml:space="preserve">
//       ${tspans}
//     </text>
//   </g>
//   <!-- small footer -->
//   <text x="${width - 12}" y="${height - 6}" font-family="sans-serif" font-size="10" fill="#6b7280" text-anchor="end">
//     Updated: ${new Date().toISOString().slice(0,19).replace('T',' ')}
//   </text>
// </svg>`;

//     res.setHeader('Content-Type', 'image/svg+xml; charset=utf-8');
//     res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=7200');
//     res.status(200).send(svg);

//   } catch (err) {
//     console.error(err);
//     res.setHeader('Content-Type', 'text/plain; charset=utf-8');
//     res.status(500).send('Internal error: ' + (err && err.message ? err.message : String(err)));
//   }
// }
