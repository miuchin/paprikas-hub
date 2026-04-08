
(function(){
  const BRIDGE = {config:null, rules:null, aliasMap:null, context:null};
  function normalize(s){
    return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
  }
  async function getJson(path){
    try{ const r = await fetch(path, {cache:'no-store'}); if (!r.ok) return null; return await r.json(); }catch(_e){ return null; }
  }
  async function loadContext(){
    try{ if (window.SINET_SHARED_CONTEXT && typeof window.SINET_SHARED_CONTEXT === 'object') return window.SINET_SHARED_CONTEXT; }catch(_e){}
    try{ const raw = localStorage.getItem('PaprikasHubSharedContextV1'); if (raw){ const x = JSON.parse(raw); if (x && typeof x === 'object') return x; } }catch(_e){}
    return await getJson('data/bridge/shared_context_example.json');
  }
  function getActiveProfiles(){
    const ctx = BRIDGE.context || {};
    const tags = Array.isArray(ctx.health_tags) ? ctx.health_tags : [];
    const base = ctx.active_profile ? [String(ctx.active_profile)] : [];
    return Array.from(new Set(base.concat(tags.map(String)).filter(Boolean)));
  }
  function collectCanonicals(recipe){
    const arr = [];
    (recipe && recipe.sastojci || []).forEach(x => {
      const raw = normalize(x && x.item || '');
      if (!raw) return;
      const exact = BRIDGE.aliasMap && BRIDGE.aliasMap[raw];
      if (exact) { arr.push(exact); return; }
      if (BRIDGE.aliasMap){
        for (const k in BRIDGE.aliasMap){
          if (raw.includes(k)){ arr.push(BRIDGE.aliasMap[k]); break; }
        }
      }
    });
    return Array.from(new Set(arr));
  }
  function scoreRecipeBridge(recipe){
    const active = getActiveProfiles();
    if (!active.length || !BRIDGE.rules) return {score:0,label:'bez profila',why:['Nema aktivnog profila'],className:'bridge-neutral'};
    const canon = collectCanonicals(recipe);
    let score = 0; const why = [];
    let avoidHit = false, cautionHit = false;
    active.forEach(tag => {
      const rule = BRIDGE.rules[tag];
      if (!rule) return;
      (rule.prefer||[]).forEach(id=>{ if (canon.includes(id)){ score += 2; why.push('✓ ' + id); } });
      (rule.caution||[]).forEach(id=>{ if (canon.includes(id)){ score -= 2; cautionHit = true; why.push('△ ' + id); } });
      (rule.avoid||[]).forEach(id=>{ if (canon.includes(id)){ score -= 5; avoidHit = true; why.push('✕ ' + id); } });
    });
    let label='neutralno', className='bridge-neutral';
    if (avoidHit || score <= -4){ label='nije idealno danas'; className='bridge-avoid'; }
    else if (cautionHit || score < 1){ label='oprez'; className='bridge-caution'; }
    else if (score >= 1){ label='preporučeno'; className='bridge-good'; }
    return {score, label, why: why.slice(0,6), className};
  }
  function renderBar(){
    const total = document.getElementById('phRecipesTotalLine');
    if (!total) return;
    let box = document.getElementById('phBridgeBar');
    if (!box){
      box = document.createElement('div');
      box.id='phBridgeBar';
      box.className='note';
      box.style.marginTop='10px';
      total.insertAdjacentElement('afterend', box);
    }
    const active = getActiveProfiles();
    const chips = active.length ? active.map(x=>`<span class="chip">${x}</span>`).join(' ') : '<span class="chip">neutral</span>';
    box.innerHTML = `<strong>🌉 Bridge v1</strong> • profil: <strong>${(BRIDGE.context&&BRIDGE.context.display_name)|| (BRIDGE.context&&BRIDGE.context.active_profile) || 'neutral'}</strong><div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">${chips}<label style="margin-left:auto;display:flex;gap:6px;align-items:center"><input id="phBridgeBetterOnly" type="checkbox"> prikaži samo bolje</label></div>`;
    const cb = document.getElementById('phBridgeBetterOnly');
    if (cb && !cb._bridgeBound){ cb._bridgeBound = true; cb.addEventListener('change', ()=>{ try{ window.phRecipesRender && window.phRecipesRender(); }catch(_e){} }); }
  }
  function decorate(){
    const list = document.getElementById('phRecipesList');
    if (!list || !window.PH_RECIPES || !window.PH_RECIPES.ready || !window.phRecipesGetCombined) return;
    const combined = window.phRecipesGetCombined();
    const byId = {};
    combined.forEach(r=>{ if (r && r.id) byId[String(r.id)] = r; });
    const betterOnly = !!(document.getElementById('phBridgeBetterOnly')||{}).checked;
    list.querySelectorAll('details[data-ph-recipe-id]').forEach(el => {
      const id = el.getAttribute('data-ph-recipe-id');
      const rec = byId[id]; if (!rec) return;
      const res = scoreRecipeBridge(rec);
      let badge = el.querySelector('.ph-bridge-badge');
      if (!badge){
        badge = document.createElement('span');
        badge.className = 'ph-bridge-badge chip';
        const sum = el.querySelector('summary > div > div');
        if (sum) sum.appendChild(badge);
      }
      badge.textContent = `🌉 ${res.label} (${res.score})`;
      badge.className = 'ph-bridge-badge chip ' + res.className;
      let why = el.querySelector('.ph-bridge-why');
      if (!why){
        why = document.createElement('div');
        why.className = 'note ph-bridge-why';
        const body = el.querySelector('div[style*="margin-top:8px"]') || el;
        body.insertBefore(why, body.firstChild);
      }
      why.innerHTML = `<strong>Zašto:</strong> ${res.why.length ? res.why.join(' · ') : 'nema pogodaka iz health-tag pravila.'}`;
      el.style.display = (betterOnly && res.label !== 'preporučeno') ? 'none' : '';
    });
  }
  async function boot(){
    BRIDGE.config = await getJson('data/bridge/bridge_config.json') || {};
    BRIDGE.rules = await getJson('data/bridge/health_tag_rules.json') || {};
    BRIDGE.aliasMap = await getJson('data/catalog/ingredient_alias_map.json') || {};
    const normMap = {}; Object.keys(BRIDGE.aliasMap).forEach(k=>{ normMap[normalize(k)] = BRIDGE.aliasMap[k]; }); BRIDGE.aliasMap = normMap;
    BRIDGE.context = await loadContext() || {};
    renderBar();
    const old = window.phRecipesRender;
    if (typeof old === 'function' && !old._bridgeWrapped){
      const wrapped = function(){ const rv = old.apply(this, arguments); try{ renderBar(); decorate(); }catch(_e){} return rv; };
      wrapped._bridgeWrapped = true;
      window.phRecipesRender = wrapped;
      try{ window.phRecipesRender(); }catch(_e){}
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
