# Modernização do site público — 2026

## 1. Objetivo
Redesenho visual e funcional da página inicial pública (`/`) da Igreja Verbo da Vida Braga. Mantém a arquitetura Flask + Jinja existente, sem alterar rotas, autenticação, permissões ou base de dados.

## 2. Estado anterior
- Cabeçalho com pesquisa permanente ocupando espaço e links em linha.
- Hero com `min-height: 62vh` e título grande, com espaço vazio excessivo.
- Secções empilhadas com estilos genéricos; falta de hierarquia visual.
- Rodapé simples.

## 3. Arquitetura identificada
- Backend: FastAPI (`appgenesis`), templates Jinja (`templates/base.html`, `templates/landing.html`, partials `public_header.html` e `public_footer.html`).
- Estilos: `static/css/genesis-public.css` (existente) e `static/css/site-moderno.css` (novo).
- Dados de eventos: `/api/eventos-agenda`, alimentado por `scripts/agenda/eventos_do_mes.py` via systemd timer diário.
- Imagens estáticas: volume Docker `app_static_prod` montado em `/app/static`. Ficheiros novos em `static/` **têm de ser copiados para o volume** (o volume sobrepõe a imagem).

## 4. Decisões de design
- Paleta (tokens em `:root` de `site-moderno.css`): fundo `#101014`, secundário `#1b1b20`, papel `#f7f4ef`, dourado discreto `#c8a66a`.
- Tipografia: mantém `Instrument Serif` (títulos) e `Source Sans 3` (texto), já carregadas em `base.html`, para evitar novos pedidos de fontes.
- Hero com imagem de fundo + gradiente escuro. Imagem provisória: cartaz existente (`static/img/hero-placeholder.jpg`), a substituir por fotografia real da igreja.
- Cabeçalho sem nome da marca (só logótipo), links em linha no desktop e painel no mobile, pesquisa em painel acionado por ícone.
- Animações GSAP 3.12.5 + ScrollTrigger (cdnjs) apenas com `prefers-reduced-motion` desativado. Sem GSAP, o conteúdo fica visível.
- Carrossel de eventos: deslize horizontal, rotação aleatória a cada 3 s, pausa com rato/toque.
- "Próximo encontro" calculado no browser com fuso `Europe/Lisbon` (domingo 10h00, quarta 20h30).

## 5. Componentes criados
- Classes `vb-hdr*` (cabeçalho), `vb-hero*`, `vb-sec*`, `vb-cartao`, `vb-culto`, `vb-video`, `vb-visita*`, `vb-final`, `vb-rodape*`.
- JSON-LD `Church` com morada e horários (dados já publicados no site).

## 6. Componentes modificados
- `templates/partials/public_header.html` (reescrito).
- `templates/partials/public_footer.html` (reescrito).
- `templates/landing.html` (reescrito; mesma fonte de dados de eventos).

## 7. Páginas alteradas
- Página inicial (`/`).
- Não alterado: login e recuperação de palavra-passe (ver pendências).

## 8. Integrações preservadas
- `/api/eventos-agenda` e carrossel de eventos.
- Instagram (embed existente).
- Links do Google Maps e YouTube oficiais.
- Pesquisa: mesmo formulário `GET /?q=`.

## 9. Performance
- Imagem de fundo com `background` CSS; sem imagens novas pesadas.
- GSAP carregado com `defer`.
- Sem novas fontes.

## 10. Acessibilidade
- Foco visível (`:focus-visible`).
- Botões de ícone com `aria-label` e `aria-expanded`.
- Menu e pesquisa fecham com Escape; foco devolvido ao botão.
- Link de salto para o conteúdo mantido.
- `prefers-reduced-motion` respeitado em CSS e JS.

## 11. Testes realizados
- Renderização Jinja da página inicial (`jinja2`) sem erros.
- Validação de sintaxe dos scripts inline com `node --check`.
- Lógica do próximo encontro verificada com datas de exemplo.
- Verificação visual em produção: ver secção "Validação" do PR.

## 12. Problemas conhecidos e pendências
- **Fotografias reais** da igreja ainda não existem: a imagem provisória é o cartaz EKBALLO.
- **Login e recuperação de palavra-passe** não foram redesenhados: partilham `login.css` com o modo administrador e os fluxos de palavra-passe. Fica para uma iteração própria.
- **Eventos com o mesmo cartaz**: a sheet usa o mesmo `ID_DA_IMAGEM` em vários eventos. Cada evento precisa do seu ficheiro.
- **Chá de mulheres**: imagem `779ec938.ID_DA_IMAGEM.154809.png` ainda não está na pasta do Drive.
- **Vídeo de fundo**: não implementado (não há vídeo autorizado).
- **Google Earth Studio**: não preparado; sem ativo real.
- **Testes automáticos do repositório** já falhavam em `master` (12 testes não relacionados).

## 13. Próximos passos
1. Substituir `static/img/hero-placeholder.jpg` por fotografia real (com autorização de uso).
2. Dar a cada evento a sua imagem na sheet.
3. Redesenhar login mantendo a lógica.
4. Medir Core Web Vitals e Lighthouse em produção.

## 14. Validação em produção
1. `curl -s https://verbodavidabraga.pt/health` → 200.
2. Página inicial: título "Verbo da Vida Braga | Uma Igreja, Uma Família".
3. Cabeçalho: logótipo sem nome; menu mobile abre e fecha com botão e Escape.
4. Eventos: carrossel sem barra de scroll, rotação a cada 3 s.
5. Sem scroll horizontal em 375 px e em 1440 px.

## 15. Reversão
- `git revert` do merge do PR da modernização.
- Recriar o volume com o CSS/imagens anteriores: os ficheiros novos (`site-moderno.css`, `hero-placeholder.jpg`) podem ser removidos do volume sem efeito no resto do site.
- Backup de base de dados antes de cada deploy: `/opt/appgenesis/backups/`.

## 16. Notas de deploy
- O volume `app_static_prod` não é atualizado pela imagem Docker. Após `git pull`, copiar os ficheiros novos de `static/` para `/var/lib/docker/volumes/app_static_prod/_data/`.
- Não copiar `static/profile_photos/` nem sobrepor `static/img/` com pastas inteiras (contém uploads).
