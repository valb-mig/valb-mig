// Gera assets/neofetch.svg com o mesmo código da rota /api/fetch. Roda todo dia pela GitHub Action.
import { writeFileSync } from 'node:fs';
import { collect, render } from '../api/fetch.js';

const out = process.argv[2] ?? 'assets/neofetch.svg';
const data = await collect();
if (!data.waka?.languages?.length || !data.user) {
  // Melhor manter o painel de ontem do que publicar um "offline".
  console.error('WakaTime ou GitHub fora do ar; mantendo o painel atual.');
  process.exit(0);
}
writeFileSync(out, render(data));
console.log(`${out} atualizado`);
