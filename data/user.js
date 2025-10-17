import fetch from "node-fetch";

export default async function handler(req, res) {
  const username = "valb-mig";

  const headers = {
    "User-Agent": "ascii-profile",
    "Accept": "application/vnd.github+json"
  };

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

  const ascii = `
╭───────────────────────────────╮
│ user        │ ${username}
│ langs       │ ${topLangs}
│ commits     │ ${commits ?? "??"}
│ stars       │ ${stars}
│ pull reqs   │ ${prs}
│ issues      │ ${issues}
╰───────────────────────────────╯
`;

  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.status(200).send(ascii);
}
