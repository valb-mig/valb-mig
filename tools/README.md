# tools

Gera os SVGs de `assets/` e a fonte embutida do painel (`api/_font.js`).

```bash
python -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/build.py tools/fonts tools/hand.png assets api
```

Precisa do ImageMagick (`magick`) no PATH: é ele que lê `hand.png` pra montar a mão em ASCII do topo.
Textos, projetos e cores ficam em `tools/build.py`. O painel neofetch é gerado em tempo real por `api/fetch.js`, na Vercel.

Fontes (SIL Open Font License, ver os `OFL-*.txt`): Outfit e Caskaydia Mono (Cascadia Code com patch do Nerd Fonts), cortada pros caracteres usados.
