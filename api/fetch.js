// Painel estilo neofetch do README: setup fixo + WakaTime (pelo endpoint público do blog) + números do GitHub.
import { MONO_WOFF } from './_font.js';

const USER = 'valb-mig';
const WAKATIME_URL = 'https://valb-blog.vercel.app/api/wakatime';

const C = {
  bg: '#0b0b0d', panel: '#0f0f12', line: '#24242b', line2: '#2f2f37',
  text: '#c4c4cb', muted: '#86868f', dim: '#55555e',
  indigo: '#2b1b8f', purple: '#7b1fa2', magenta: '#d0268f', orange: '#f4a259', white: '#ffffff',
};

const INFO = [
  ['role', 'backend developer · 4+ years'],
  ['os', 'Arch Linux'],
  ['wm', 'bspwm'],
  ['shell', 'zsh · kitty'],
  ['editor', 'VS Code · nvim · Claude Code'],
  ['stack', 'PHP · Laravel · TypeScript · Node'],
  ['infra', 'Docker · systemd · Tailscale'],
  ['uptime', '21 years'],
  ['process', 'code(); lift(); cook(); repeat();'],
  ['location', `8° 04' 03"S 34° 55' 00"W`],
];

// Laptop em ASCII: moldura no degradê da paleta, tela com um mini terminal.
const SW = 22; // largura interna da tela
const SCREEN = ['', '$ whoami', 'valb', '$ cd ~/kronofit', '$ _', ''];
const LAPTOP = [
  [`   .${'-'.repeat(SW + 4)}.`],
  [`   | .${'-'.repeat(SW)}. |`],
  ...SCREEN.map((l) => [`   | | `, l, `${' '.repeat(SW - 1 - l.length)}| |`]),
  [`   | '${'-'.repeat(SW)}' |`],
  [`   '${'-'.repeat(SW + 4)}'`],
  [`  /  ${':'.repeat(SW + 2)}  \\`],
  [` /  ${':'.repeat(SW + 4)}  \\`],
  [`'${'-'.repeat(SW + 10)}'`],
];

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

async function getJSON(url) {
  const headers = { 'User-Agent': 'valb-mig-readme', Accept: 'application/json' };
  // Na GitHub Action o token evita o limite de 60 requisições por hora dos runners compartilhados.
  if (process.env.GITHUB_TOKEN && url.startsWith('https://api.github.com/')) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const res = await fetch(url, { headers, signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.json();
}

const shortTime = (text = '') => text.replace(/ hrs?/g, 'h').replace(/ mins?/g, 'm').replace(/ secs?/g, 's');

export function render({ waka, user, stars }) {
  const W = 1000;
  const H = 400;
  const out = [];
  out.push(`<rect x=".5" y=".5" width="${W - 1}" height="${H - 1}" rx="16" fill="${C.bg}" stroke="${C.line}"/>`);
  out.push(`<path d="M.5,34 H${W - 0.5}" stroke="${C.line}"/>`);
  [C.indigo, C.magenta, C.orange].forEach((c, i) => out.push(`<circle cx="${20 + i * 14}" cy="17.5" r="4.4" fill="${c}"/>`));
  out.push(`<text x="${W / 2}" y="21.5" font-size="11" fill="${C.dim}" text-anchor="middle">valb@arch: ~/neofetch</text>`);

  // laptop
  const lx = 44, ly = 104, lh = 17;
  LAPTOP.forEach(([frame, screen, rest], r) => {
    const y = ly + r * lh;
    let line = `<tspan fill="url(#logo)">${esc(frame)}</tspan>`;
    if (screen !== undefined) {
      const body = screen.endsWith('_')
        ? `<tspan fill="${C.white}">${esc(screen.slice(0, -1))}</tspan><tspan class="cursor" fill="${C.orange}">_</tspan>`
        : `<tspan fill="${screen.startsWith('$') ? C.orange : C.white}">${esc(screen)}</tspan>`;
      line += body + `<tspan fill="url(#logo)">${esc(rest)}</tspan>`;
    }
    out.push(`<text x="${lx}" y="${y}" font-size="12" filter="url(#glow)">${line}</text>`);
  });

  // informações
  const ix = 300;
  out.push(`<text x="${ix}" y="80" font-size="16"><tspan fill="${C.orange}">valb</tspan><tspan fill="${C.dim}">@</tspan><tspan fill="${C.magenta}">arch</tspan></text>`);
  out.push(`<text x="${ix}" y="98" font-size="13" fill="${C.line2}">─────────</text>`);
  INFO.forEach(([k, v], i) => {
    const y = 126 + i * 22;
    out.push(`<text x="${ix}" y="${y}" font-size="13"><tspan fill="${C.magenta}">${esc(k)}</tspan><tspan x="${ix + 84}" fill="${C.text}">${esc(v)}</tspan></text>`);
  });
  // blocos de cor, como no neofetch
  [C.indigo, C.purple, C.magenta, C.orange, C.white, C.line2, C.muted, C.text].forEach((c, i) => out.push(`<rect x="${ix + i * 30}" y="356" width="26" height="14" rx="2" fill="${c}"/>`));

  // WakaTime
  const wx = 690, wy = 60, ww = 280;
  out.push(`<rect x="${wx}" y="${wy}" width="${ww}" height="230" rx="12" fill="${C.panel}" stroke="${C.line}"/>`);
  out.push(`<text x="${wx + 18}" y="${wy + 26}" font-size="11" fill="${C.dim}">wakatime · last 7 days</text>`);
  if (waka?.languages?.length) {
    out.push(`<text x="${wx + 18}" y="${wy + 62}" font-size="26" fill="${C.text}">${esc(shortTime(waka.totalText))}</text>`);
    waka.languages.slice(0, 4).forEach((l, i) => {
      const y = wy + 96 + i * 34;
      out.push(`<text x="${wx + 18}" y="${y}" font-size="12" fill="${C.text}">${esc(l.name)}</text>`);
      out.push(`<text x="${wx + ww - 18}" y="${y}" font-size="11" fill="${C.muted}" text-anchor="end">${l.percent.toFixed(1)}%</text>`);
      out.push(`<rect x="${wx + 18}" y="${y + 8}" width="${ww - 36}" height="5" rx="2.5" fill="${C.line}"/>`);
      out.push(`<rect x="${wx + 18}" y="${y + 8}" width="${Math.max(4, ((ww - 36) * l.percent) / 100).toFixed(1)}" height="5" rx="2.5" fill="url(#bar)"/>`);
    });
  } else {
    out.push(`<text x="${wx + 18}" y="${wy + 62}" font-size="13" fill="${C.dim}">offline</text>`);
  }

  // GitHub
  const gh = user ? `${user.public_repos} repos · ★ ${stars} · ${user.followers} followers` : 'offline';
  out.push(`<text x="${wx}" y="318" font-size="12"><tspan fill="${C.magenta}">github</tspan><tspan x="${wx + 60}" fill="${C.text}">${esc(gh)}</tspan></text>`);
  out.push(`<text x="${wx}" y="342" font-size="11" fill="${C.dim}">updated ${new Date().toISOString().slice(0, 10)}</text>`);

  const defs = `
    <linearGradient id="logo" gradientUnits="userSpaceOnUse" x1="0" y1="96" x2="0" y2="320"><stop offset="0" stop-color="${C.orange}"/><stop offset=".45" stop-color="${C.magenta}"/><stop offset=".8" stop-color="${C.purple}"/><stop offset="1" stop-color="#5a3bd6"/></linearGradient>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${C.purple}"/><stop offset=".6" stop-color="${C.magenta}"/><stop offset="1" stop-color="${C.orange}"/></linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`;
  const css = `@font-face{font-family:'mono';src:url(data:font/woff;base64,${MONO_WOFF}) format('woff')}text{font-family:'mono',monospace;white-space:pre}@media (prefers-reduced-motion:no-preference){.cursor{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="valb@arch neofetch: setup, WakaTime e GitHub"><defs><style>${css}</style>${defs}</defs>${out.join('')}</svg>`;
}

/** Busca WakaTime e GitHub; o que falhar vem como null. */
export async function collect() {
  const [waka, user, repos] = await Promise.allSettled([
    getJSON(WAKATIME_URL),
    getJSON(`https://api.github.com/users/${USER}`),
    getJSON(`https://api.github.com/users/${USER}/repos?per_page=100`),
  ]);
  return {
    waka: waka.status === 'fulfilled' ? waka.value : null,
    user: user.status === 'fulfilled' ? user.value : null,
    stars: repos.status === 'fulfilled' ? repos.value.filter((r) => !r.fork).reduce((n, r) => n + r.stargazers_count, 0) : 0,
  };
}

export default async function handler(req, res) {
  const svg = render(await collect());
  res.setHeader('Content-Type', 'image/svg+xml; charset=utf-8');
  res.setHeader('Cache-Control', 'public, s-maxage=3600, stale-while-revalidate=86400');
  res.status(200).send(svg);
}
