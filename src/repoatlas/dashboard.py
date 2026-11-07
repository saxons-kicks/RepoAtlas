"""Self-contained, offline HTML dashboard."""

from __future__ import annotations

import html
import json
from typing import Any


def render_dashboard(catalog: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    payload = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    title = "RepoAtlas · Catálogo de repositórios"
    compared = summary.get("comparison_performed", False)
    subtitle = "Comparação concluída · Identidade canônica e metadados" if compared else "Importação de favoritos concluída · Stars ainda não comparados"
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#0b1020;--panel:#121a2d;--panel2:#18243b;--text:#e8eef9;--muted:#9daec8;--line:#263653;--accent:#7dd3fc;--good:#86efac;--warn:#fcd34d;--bad:#fca5a5}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 12% 0%,#1b2d4e 0,transparent 35%),var(--bg);color:var(--text);font:14px/1.5 Inter,Segoe UI,system-ui,sans-serif}}
main{{max-width:1380px;margin:0 auto;padding:32px 22px 64px}}header{{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap;margin-bottom:24px}}
.eyebrow{{color:var(--accent);font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}}h1{{font-size:clamp(28px,5vw,42px);letter-spacing:-.04em;margin:5px 0}}.muted{{color:var(--muted)}}
.pill{{border:1px solid var(--line);border-radius:99px;padding:7px 12px;color:var(--muted);font-size:12px}}
.cards{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:22px 0 18px}}.card{{background:linear-gradient(145deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:16px;padding:16px}}
.card b{{display:block;font-size:30px;letter-spacing:-.04em}}.card span{{font-size:12px;color:var(--muted)}}
.toolbar{{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 14px}}input,select{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:11px 13px;color:var(--text);font:inherit}}input{{flex:1;min-width:230px}}select{{min-width:160px}}
.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:16px;background:rgba(18,26,45,.8)}}table{{width:100%;border-collapse:collapse;min-width:1040px}}th,td{{padding:13px 15px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);background:#111a2b;position:sticky;top:0}}tr:last-child td{{border-bottom:0}}a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}.repo{{font-weight:700}}.desc{{color:var(--muted);max-width:440px}}.tag{{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:3px 8px;margin:2px 4px 2px 0;font-size:11px;color:#c8d7ed}}.status{{font-size:11px;font-weight:700;white-space:nowrap}}.both{{color:var(--good)}}.star_only{{color:var(--accent)}}.bookmark_only{{color:var(--warn)}}.not_compared{{color:var(--muted)}}.private{{color:var(--bad);font-size:11px}}.meta-warning{{color:var(--warn);font-size:11px}}.relation{{color:#c8d7ed;font-size:12px}}.empty{{padding:32px;text-align:center;color:var(--muted)}}footer{{margin-top:18px;color:var(--muted);font-size:11px}}
@media(max-width:1050px){{.cards{{grid-template-columns:repeat(3,minmax(0,1fr))}}}}@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,minmax(0,1fr))}}main{{padding:22px 14px 44px}}}}
</style></head><body><main>
<header><div><div class="eyebrow">Local-first repository intelligence</div><h1>RepoAtlas</h1><div class="muted">{html.escape(subtitle)}</div></div><div class="pill">Sem telemetria · Funciona offline</div></header>
<section class="cards">
<div class="card"><b>{summary.get('unique_repositories',0)}</b><span>Repositórios canônicos</span></div>
<div class="card"><b>{summary.get('both',0)}</b><span>Em Stars e favoritos</span></div>
<div class="card"><b>{summary.get('star_only',0)}</b><span>Somente GitHub Stars</span></div>
<div class="card"><b>{summary.get('bookmark_only',0) if compared else summary.get('unique_github_repositories_in_bookmarks',0)}</b><span>{'Somente favoritos' if compared else 'Repositórios nos favoritos'}</span></div>
<div class="card"><b>{summary.get('fork_repositories',0)}</b><span>Forks identificados</span></div>
</section>
<div class="toolbar">
<input id="search" type="search" placeholder="Buscar repo, descrição, alias, tópico, fork..." autocomplete="off">
<select id="status"><option value="all">Todos os status</option><option value="both">Em ambos</option><option value="star_only">Somente Star</option><option value="bookmark_only">Somente favorito</option><option value="not_compared">Não comparado</option></select>
<select id="category"><option value="all">Todas as categorias</option></select>
<select id="kind"><option value="all">Todos os tipos</option><option value="fork">Somente forks</option><option value="original">Projetos originais</option><option value="archived">Arquivados</option><option value="active">Não arquivados</option></select>
</div>
<div class="table-wrap"><table><thead><tr><th>Repositório</th><th>Status</th><th>Categoria / Tags</th><th>Linguagem</th><th>Relação</th><th>Atividade</th></tr></thead><tbody id="rows"></tbody></table><div id="empty" class="empty" hidden>Nenhum repositório corresponde aos filtros.</div></div>
<footer>Catálogo local e offline. Identidade primária pelo ID oficial do GitHub; owner/repo é usado como fallback. Aliases e forks são preservados como relações, não tratados como projetos idênticos. Referências privadas continuam sinalizadas apenas nesta instalação.</footer>
</main>
<script id="repo-data" type="application/json">{payload}</script>
<script>
const repos=JSON.parse(document.getElementById('repo-data').textContent);const $=id=>document.getElementById(id);const statusLabels={{both:'Em ambos',star_only:'Somente Star',bookmark_only:'Somente favorito',not_compared:'Não comparado'}};
const categories=[...new Set(repos.flatMap(r=>r.category_labels||[]))].sort();for(const c of categories){{const o=document.createElement('option');o.value=c;o.textContent=c;$('category').append(o)}}
function esc(s){{return String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]))}}
function render(){{const q=$('search').value.trim().toLowerCase(),st=$('status').value,cat=$('category').value,kind=$('kind').value;const list=repos.filter(r=>{{const hay=[r.full_name,r.description,r.language,r.parent_full_name,r.source_full_name,...(r.aliases||[]),...(r.topics||[]),...(r.tags||[]),...(r.bookmark_titles||[])].join(' ').toLowerCase();const kindOk=kind==='all'||(kind==='fork'&&r.fork)||(kind==='original'&&!r.fork)||(kind==='archived'&&r.archived)||(kind==='active'&&!r.archived);return (!q||hay.includes(q))&&(st==='all'||r.status===st)&&(cat==='all'||(r.category_labels||[]).includes(cat))&&kindOk}});$('rows').innerHTML=list.map(r=>{{const root=r.source_full_name||r.parent_full_name;const relation=r.fork?`Fork de ${{esc(root||'origem não identificada')}}`: 'Projeto original';const warnings=['not_found','forbidden','rate_limited','unavailable','error','auth_missing'].includes(r.metadata_status);return `<tr><td><a class="repo" href="${{esc(r.url)}}" target="_blank" rel="noopener noreferrer">${{esc(r.full_name)}}</a><div class="desc">${{esc(r.description||'Sem descrição disponível')}}</div>${{r.aliases?.length?`<div class="relation">Alias: ${{r.aliases.map(esc).join(', ')}}</div>`:''}}${{r.private_context?'<div class="private">Contexto privado local</div>':''}}${{warnings?`<div class="meta-warning">Metadados: ${{esc(r.metadata_status)}}</div>`:''}}</td><td><span class="status ${{esc(r.status)}}">${{esc(statusLabels[r.status]||r.status)}}</span></td><td>${{(r.category_labels||[]).map(c=>`<span class="tag">${{esc(c)}}</span>`).join('')}}<div class="relation">${{(r.topics||[]).slice(0,5).map(esc).join(' · ')}}</div></td><td>${{esc(r.language||'—')}}</td><td class="relation">${{relation}}</td><td>${{esc(r.pushed_at?new Date(r.pushed_at).toLocaleDateString('pt-BR'):'—')}}${{r.archived?' · Arquivado':''}}</td></tr>`}}).join('');$('empty').hidden=list.length>0}}
for(const id of ['search','status','category','kind'])$(id).addEventListener(id==='search'?'input':'change',render);render();
</script></body></html>'''
