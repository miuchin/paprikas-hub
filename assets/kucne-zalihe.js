(function(){
  const VERSION = 'KZ-MVP v0.1.10';
  const DB_NAME = 'paprikasHubHouseholdV1';
  const DB_VERSION = 1;
  const SEED_BASE = '../data/seed/kucne-zalihe/';
  const NUTRI_CANON = '../data/NUTRI_STL.json';
  const LEGACY_BRIDGE = '../data/catalog/ingredient_nutri_seed.json';
  const STORE_NAMES = [
    'food_items','food_categories','units','storage_locations','stock_entries','inventory_movements',
    'purchase_logs','purchase_log_items','menu_plan_reservations','menu_plans_local',
    'leftover_entries','waste_log','household_settings'
  ];

  const GROUP_TO_CATEGORY = {
    'Povrće':'vegetables',
    'Voće':'fruits',
    'Mlečno':'dairy',
    'Meso':'meat',
    'Riba':'fish',
    'Jaja':'eggs',
    'Žitarice':'grains',
    'Žitarice i pseudožitarice':'grains',
    'Mahunarke':'legumes',
    'Biljni proteini':'legumes',
    'Masti':'spices',
    'Pića':'other',
    'Orašasti':'other',
    'Semenke':'other',
    'Slatkiši':'other',
    'Grickalice':'other',
    'Iznutrice':'meat'
  };

  const STORE_HINTS = {
    vegetables:'fridge',
    fruits:'counter',
    dairy:'fridge',
    meat:'fridge',
    fish:'fridge',
    eggs:'fridge',
    grains:'pantry',
    pasta_rice:'pantry',
    legumes:'pantry',
    bread_bakery:'counter',
    spices:'pantry',
    cooked:'fridge',
    frozen:'freezer',
    other:'unspecified'
  };

  const STATUS_LABELS = {
    sealed:'Zatvoreno',
    opened:'Otvoreno',
    leftover:'Ostatak jela',
    frozen:'Zamrznuto',
    consumed:'Potrošeno',
    waste:'Bačeno'
  };

  const MOVEMENT_TYPE_LABELS = {
    purchase_in:'Ulaz iz nabavke',
    manual_in:'Ručni ulaz',
    menu_reserved:'Rezervisano za plan',
    meal_out:'Potrošeno',
    waste_out:'Otpis / bačeno',
    transfer:'Premeštaj',
    freeze:'Zamrznuto',
    thaw:'Odmrznuto',
    return_in:'Vraćeno u zalihu',
    adjustment:'Korekcija'
  };

  function normalizeText(value){
    return String(value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g,'')
      .replace(/đ/g,'dj')
      .replace(/[^a-z0-9]+/g,' ')
      .trim();
  }

  function escapeHtml(value){
    return String(value ?? '')
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;')
      .replace(/'/g,'&#39;');
  }

  function makeId(prefix){
    return prefix + '-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2,8);
  }

  function isoNow(){
    return new Date().toISOString();
  }

  function formatDate(value){
    if(!value) return '—';
    const d = new Date(value);
    if(Number.isNaN(d.getTime())) return String(value);
    return d.toLocaleDateString('sr-RS');
  }

  function daysUntil(value){
    if(!value) return null;
    const d = new Date(value);
    if(Number.isNaN(d.getTime())) return null;
    const now = new Date();
    const ms = d.setHours(0,0,0,0) - new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    return Math.round(ms / 86400000);
  }

  function priorityLabel(priority){
    return ({expired:'Isteklo', critical:'Hitno', high:'Visoko', normal:'Srednje', low:'Nisko'})[priority] || priority;
  }

  function mapNutriGroupToCategory(group, name){
    if(GROUP_TO_CATEGORY[group]) return GROUP_TO_CATEGORY[group];
    const t = normalizeText(name);
    if(/hleb|pecivo|kora|tost/.test(t)) return 'bread_bakery';
    if(/testenin|makaron|spaget|pirinac|pirina[cč]|rezanac/.test(t)) return 'pasta_rice';
    if(/supa|corba|čorba|gulas|gula[sš]|varivo|paprikas|paprika[sš]|sos|umak/.test(t)) return 'cooked';
    if(/sladoled|smrznut|zamrznut/.test(t)) return 'frozen';
    if(/so|secer|šećer|sirce|sirće|ulje|zac|zač|biber/.test(t)) return 'spices';
    return 'other';
  }

  function inferDefaultUnitFromNutri(name, group){
    const t = normalizeText(name);
    const g = String(group || '');
    if(g === 'Jaja' || /jaje|jaja/.test(t)) return 'pcs';
    if(/mleko|jogurt|kefir|surutk|sok|voda|napitak|vino|pivo/.test(t)) return 'ml';
    if(/ulje/.test(t)) return 'ml';
    if(/tegla|konzerva|pakovanje|paket/.test(t)) return 'pack';
    if(/hleb/.test(t)) return 'pcs';
    return 'g';
  }

  function inferPerishableLevel(categoryId, status){
    if(status === 'leftover' || status === 'opened') return 'high';
    if(['meat','fish','dairy','eggs','cooked'].includes(categoryId)) return 'high';
    if(['vegetables','fruits','bread_bakery'].includes(categoryId)) return 'medium';
    return 'low';
  }

  function calcPriority(entry){
    const expiryDays = daysUntil(entry.expiry_date);
    const bestBeforeDays = daysUntil(entry.best_before_date);
    if(expiryDays !== null && expiryDays < 0) return 'expired';
    if(entry.status === 'leftover') return 'critical';
    if(entry.status === 'opened') return 'high';
    if(expiryDays !== null && expiryDays <= 1) return 'critical';
    if(bestBeforeDays !== null && bestBeforeDays <= 1) return 'high';
    if(entry.perishable_level === 'high') return 'high';
    if(entry.perishable_level === 'medium') return 'normal';
    return 'low';
  }

  function openDb(){
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = (event) => {
        const db = event.target.result;
        if(!db.objectStoreNames.contains('food_items')){
          const s = db.createObjectStore('food_items', {keyPath:'id'});
          s.createIndex('name_normalized', 'name_normalized', {unique:false});
          s.createIndex('category_id', 'category_id', {unique:false});
          s.createIndex('source_catalog', 'source_catalog', {unique:false});
        }
        if(!db.objectStoreNames.contains('food_categories')) db.createObjectStore('food_categories', {keyPath:'id'});
        if(!db.objectStoreNames.contains('units')) db.createObjectStore('units', {keyPath:'id'});
        if(!db.objectStoreNames.contains('storage_locations')){
          const s = db.createObjectStore('storage_locations', {keyPath:'id'});
          s.createIndex('sort_order', 'sort_order', {unique:false});
          s.createIndex('is_active', 'is_active', {unique:false});
        }
        if(!db.objectStoreNames.contains('stock_entries')){
          const s = db.createObjectStore('stock_entries', {keyPath:'id'});
          s.createIndex('food_item_id', 'food_item_id', {unique:false});
          s.createIndex('location_id', 'location_id', {unique:false});
          s.createIndex('is_archived', 'is_archived', {unique:false});
          s.createIndex('entry_date', 'entry_date', {unique:false});
        }
        if(!db.objectStoreNames.contains('inventory_movements')){
          const s = db.createObjectStore('inventory_movements', {keyPath:'id'});
          s.createIndex('entry_id', 'entry_id', {unique:false});
          s.createIndex('movement_date', 'movement_date', {unique:false});
          s.createIndex('movement_type', 'movement_type', {unique:false});
        }
        if(!db.objectStoreNames.contains('purchase_logs')) db.createObjectStore('purchase_logs', {keyPath:'id'});
        if(!db.objectStoreNames.contains('purchase_log_items')) db.createObjectStore('purchase_log_items', {keyPath:'id'});
        if(!db.objectStoreNames.contains('menu_plan_reservations')) db.createObjectStore('menu_plan_reservations', {keyPath:'id'});
        if(!db.objectStoreNames.contains('menu_plans_local')) db.createObjectStore('menu_plans_local', {keyPath:'id'});
        if(!db.objectStoreNames.contains('leftover_entries')) db.createObjectStore('leftover_entries', {keyPath:'id'});
        if(!db.objectStoreNames.contains('waste_log')) db.createObjectStore('waste_log', {keyPath:'id'});
        if(!db.objectStoreNames.contains('household_settings')) db.createObjectStore('household_settings', {keyPath:'id'});
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function txDone(tx){
    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Transaction error'));
      tx.onabort = () => reject(tx.error || new Error('Transaction aborted'));
    });
  }

  async function countStore(db, name){
    return new Promise((resolve, reject) => {
      const tx = db.transaction(name, 'readonly');
      const req = tx.objectStore(name).count();
      req.onsuccess = () => resolve(req.result || 0);
      req.onerror = () => reject(req.error);
    });
  }

  async function getAll(db, storeName){
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const req = tx.objectStore(storeName).getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  }

  async function getOne(db, storeName, key){
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const req = tx.objectStore(storeName).get(key);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  }

  async function putMany(db, storeName, items){
    if(!items || !items.length) return;
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    items.forEach(item => store.put(item));
    await txDone(tx);
  }

  async function putOne(db, storeName, item){
    const tx = db.transaction(storeName, 'readwrite');
    tx.objectStore(storeName).put(item);
    await txDone(tx);
    return item;
  }

  async function seedStoreIfEmpty(db, storeName, url){
    const count = await countStore(db, storeName);
    if(count > 0) return false;
    const res = await fetch(url);
    if(!res.ok) throw new Error('Ne mogu da učitam seed: ' + url);
    const payload = await res.json();
    const items = Array.isArray(payload) ? payload : [payload];
    await putMany(db, storeName, items);
    return true;
  }

  function getNutriName(food){
    const name = food?.name;
    if(typeof name === 'string') return name;
    if(name && typeof name === 'object') return name.sr || name.en || '';
    return '';
  }

  function getNutriAliases(food){
    const aliases = [];
    const name = food?.name;
    if(name && typeof name === 'object'){
      if(name.sr_lat) aliases.push(name.sr_lat);
      if(name.sr_cyr) aliases.push(name.sr_cyr);
      if(name.en) aliases.push(name.en);
    }
    const tags = Array.isArray(food?.tags) ? food.tags : [];
    tags.forEach(tag => { if(typeof tag === 'string') aliases.push(tag); });
    return Array.from(new Set(aliases.filter(Boolean)));
  }

  function getNutriPer100g(food){
    return food?.per_100g && typeof food.per_100g === 'object' ? food.per_100g : {};
  }

  function buildFoodItemFromNutri(food){
    const name = getNutriName(food) || 'Nepoznato';
    const group = String(food?.group || '').trim();
    const categoryId = mapNutriGroupToCategory(group, name);
    const defaultUnit = inferDefaultUnitFromNutri(name, group);
    const perishableLevel = inferPerishableLevel(categoryId, 'sealed');
    return {
      id: 'nutri-' + String(food?.id || makeId('food')),
      code: String(food?.id || ''),
      name,
      name_normalized: normalizeText(name),
      synonyms: getNutriAliases(food),
      category_id: categoryId,
      default_unit: defaultUnit,
      default_unit_source: 'kucne-zalihe-inference-from-nutri',
      perishable_level: perishableLevel,
      storage_hint: STORE_HINTS[categoryId] || 'unspecified',
      nutri_ref_id: food?.id || null,
      nutri_group: group || '',
      source_catalog: 'NUTRI_STL',
      source_catalog_path: NUTRI_CANON,
      notes: 'Read-only katalog iz NutriTable / NUTRI_STL za izbor namirnice u Kućnim zalihama.',
      is_active: true,
      nutri_snapshot: food
    };
  }

  async function syncFoodItemsFromNutri(db){
    try{
      const res = await fetch(NUTRI_CANON, {cache:'no-store'});
      if(!res.ok) throw new Error('Nutri kanon nije dostupan.');
      const payload = await res.json();
      const foods = Array.isArray(payload?.foods) ? payload.foods : [];
      if(!foods.length) return {synced:0, source:'NUTRI_STL'};
      const transformed = foods.map(buildFoodItemFromNutri);
      await putMany(db, 'food_items', transformed);
      return {synced: transformed.length, source:'NUTRI_STL'};
    }catch(err){
      return {synced:0, source:'NUTRI_STL', error: String(err?.message || err)};
    }
  }

  async function seedFoodItemsFallback(db){
    const count = await countStore(db, 'food_items');
    if(count > 0) return false;

    const localSeedRes = await fetch(SEED_BASE + 'food_items.seed.json');
    if(localSeedRes.ok){
      const localSeed = await localSeedRes.json();
      await putMany(db, 'food_items', localSeed);
    }

    try{
      const bridgeRes = await fetch(LEGACY_BRIDGE, {cache:'no-store'});
      if(bridgeRes.ok){
        const bridge = await bridgeRes.json();
        const items = Array.isArray(bridge?.items) ? bridge.items.map(item => ({
          id: 'legacy-' + String(item.id || makeId('fi')),
          code: String(item.id || ''),
          name: item.naziv || 'Nepoznato',
          name_normalized: normalizeText(item.naziv || ''),
          synonyms: Array.isArray(item.varijante) ? item.varijante : [],
          category_id: mapNutriGroupToCategory('', item.naziv || ''),
          default_unit: inferDefaultUnitFromNutri(item.naziv || '', ''),
          default_unit_source: 'legacy-inference',
          perishable_level: inferPerishableLevel(mapNutriGroupToCategory('', item.naziv || ''), 'sealed'),
          storage_hint: STORE_HINTS[mapNutriGroupToCategory('', item.naziv || '')] || 'unspecified',
          nutri_ref_id: item.id || null,
          source_catalog: 'ingredient_nutri_seed',
          source_catalog_path: LEGACY_BRIDGE,
          notes: 'Fallback seed katalog iz recepata.',
          is_active: true,
          nutri_snapshot: { legacy_seed: item }
        })) : [];
        await putMany(db, 'food_items', items);
      }
    }catch(_e){ /* fallback optional */ }

    return true;
  }

  async function seedIfNeeded(){
    const db = await openDb();
    await seedStoreIfEmpty(db, 'food_categories', SEED_BASE + 'food_categories.seed.json');
    await seedStoreIfEmpty(db, 'units', SEED_BASE + 'units.seed.json');
    await seedStoreIfEmpty(db, 'storage_locations', SEED_BASE + 'default_locations.seed.json');
    await seedStoreIfEmpty(db, 'household_settings', SEED_BASE + 'household_settings.seed.json');
    await seedFoodItemsFallback(db);
    await syncFoodItemsFromNutri(db);
    db.close();
  }

  async function addLocation(payload){
    const db = await openDb();
    const item = {
      id: makeId('loc'),
      code: normalizeText(payload.name).replace(/\s+/g, '-'),
      name: String(payload.name || '').trim(),
      parent_id: payload.parent_id || null,
      location_type: payload.location_type || 'storage',
      temperature_zone: payload.temperature_zone || 'ambient',
      sort_order: Number(payload.sort_order || Date.now()),
      is_active: true,
      notes: payload.notes || ''
    };
    await putOne(db, 'storage_locations', item);
    db.close();
    return item;
  }

  function matchesFoodSelection(food, selectionText){
    const target = normalizeText(selectionText);
    if(!target) return false;
    if(food.id === selectionText) return true;
    if(food.name_normalized === target) return true;
    const display = normalizeText(foodSelectionLabel(food));
    if(display === target) return true;
    const synonyms = Array.isArray(food.synonyms) ? food.synonyms : [];
    return synonyms.some(s => normalizeText(s) === target);
  }

  function foodSelectionLabel(food){
    const group = food.nutri_group || '';
    return group ? `${food.name} — ${group}` : food.name;
  }

  async function findFoodItem(db, params){
    const items = (await getAll(db, 'food_items')).filter(x => x.is_active !== false);
    if(params.food_item_id){
      const byId = items.find(x => x.id === params.food_item_id);
      if(byId) return byId;
    }
    if(params.food_name){
      const byName = items.find(x => matchesFoodSelection(x, params.food_name));
      if(byName) return byName;
    }
    return null;
  }

  function buildNutriEntrySnapshot(foodItem){
    return {
      source_catalog: foodItem.source_catalog || null,
      source_catalog_path: foodItem.source_catalog_path || null,
      nutri_ref_id: foodItem.nutri_ref_id || null,
      nutri_group: foodItem.nutri_group || null,
      default_unit: foodItem.default_unit || null,
      default_unit_source: foodItem.default_unit_source || null,
      nutri_snapshot: foodItem.nutri_snapshot || null
    };
  }

  async function addStockEntry(payload){
    const db = await openDb();
    const foodItem = await findFoodItem(db, payload);
    if(!foodItem){
      db.close();
      throw new Error('Namirnica mora da bude izabrana iz NutriTable liste.');
    }
    const locations = await getAll(db, 'storage_locations');
    const location = locations.find(x => x.id === payload.location_id) || locations[0] || null;
    const status = payload.status || 'sealed';
    const categoryId = foodItem.category_id || payload.category_id || 'other';
    const defaultUnit = payload.unit || foodItem.default_unit || 'g';
    const entry = {
      id: makeId('entry'),
      food_item_id: foodItem.id,
      food_name_snapshot: foodItem.name,
      location_id: location ? location.id : null,
      location_name_snapshot: location ? location.name : '',
      quantity_current: Number(payload.quantity_current || 0),
      unit: defaultUnit,
      status,
      source_type: payload.source_type || 'manual',
      purchase_date: payload.purchase_date || null,
      entry_date: payload.entry_date || isoNow().slice(0,10),
      opened_date: payload.opened_date || null,
      best_before_date: payload.best_before_date || null,
      expiry_date: payload.expiry_date || null,
      priority_level: calcPriority({
        status,
        best_before_date: payload.best_before_date || null,
        expiry_date: payload.expiry_date || null,
        perishable_level: inferPerishableLevel(categoryId, status)
      }),
      batch_label: payload.batch_label || '',
      notes: payload.notes || '',
      category_id: categoryId,
      perishable_level: inferPerishableLevel(categoryId, status),
      is_archived: false,
      source_catalog: foodItem.source_catalog || null,
      nutri_ref_id: foodItem.nutri_ref_id || null,
      nutri_group: foodItem.nutri_group || null,
      nutri_entry_snapshot: buildNutriEntrySnapshot(foodItem)
    };
    await putOne(db, 'stock_entries', entry);
    await putOne(db, 'inventory_movements', {
      id: makeId('mov'),
      entry_id: entry.id,
      movement_type: payload.source_type === 'purchase' ? 'purchase_in' : 'manual_in',
      movement_date: isoNow(),
      quantity_delta: Number(entry.quantity_current || 0),
      unit: entry.unit,
      reason: 'Ulaz u zalihu',
      source_ref_type: payload.source_type || 'manual',
      source_ref_id: null,
      from_location_id: null,
      to_location_id: entry.location_id,
      notes: `${entry.food_name_snapshot} • ${entry.source_catalog || 'lokalno'}`
    });
    db.close();
    return entry;
  }

  async function updateEntryTerminal(entryId, mode){
    const db = await openDb();
    const entry = await getOne(db, 'stock_entries', entryId);
    if(!entry) throw new Error('Zapis nije pronađen.');
    const qtyBefore = Number(entry.quantity_current || 0);
    entry.is_archived = true;
    entry.quantity_current = 0;
    entry.status = mode === 'waste' ? 'waste' : 'consumed';
    entry.priority_level = 'low';
    await putOne(db, 'stock_entries', entry);
    if(mode === 'waste'){
      await putOne(db, 'waste_log', {
        id: makeId('waste'),
        entry_id: entry.id,
        food_item_id: entry.food_item_id,
        waste_date: isoNow(),
        quantity: qtyBefore,
        unit: entry.unit,
        reason: 'Ručni MVP otpis',
        notes: entry.food_name_snapshot
      });
    }
    await putOne(db, 'inventory_movements', {
      id: makeId('mov'),
      entry_id: entry.id,
      movement_type: mode === 'waste' ? 'waste_out' : 'meal_out',
      movement_date: isoNow(),
      quantity_delta: -qtyBefore,
      unit: entry.unit,
      reason: mode === 'waste' ? 'Otpis / bačeno' : 'Potrošeno',
      source_ref_type: 'manual_action',
      source_ref_id: null,
      from_location_id: entry.location_id,
      to_location_id: null,
      notes: entry.food_name_snapshot
    });
    db.close();
  }

  async function listLocations(){
    const db = await openDb();
    const items = (await getAll(db, 'storage_locations')).filter(x => x.is_active !== false)
      .sort((a,b) => (a.sort_order||0) - (b.sort_order||0) || String(a.name).localeCompare(String(b.name), 'sr'));
    db.close();
    return items;
  }

  async function listCategories(){
    const db = await openDb();
    const items = (await getAll(db, 'food_categories')).sort((a,b) => (a.sort_order||0)-(b.sort_order||0));
    db.close();
    return items;
  }

  async function listUnits(){
    const db = await openDb();
    const items = await getAll(db, 'units');
    db.close();
    return items;
  }

  async function listFoodSuggestions(limit){
    const db = await openDb();
    const items = (await getAll(db, 'food_items'))
      .filter(x => x.is_active !== false)
      .sort((a,b) => String(a.name).localeCompare(String(b.name), 'sr'));
    db.close();
    const sliced = items.slice(0, typeof limit === 'number' ? limit : 1000);
    return sliced.map(item => ({
      ...item,
      selection_label: foodSelectionLabel(item)
    }));
  }

  async function getFoodItemDetails(foodItemIdOrText){
    const db = await openDb();
    const items = (await getAll(db, 'food_items')).filter(x => x.is_active !== false);
    const found = items.find(x => x.id === foodItemIdOrText || matchesFoodSelection(x, foodItemIdOrText)) || null;
    db.close();
    return found;
  }

  async function listActiveStock(){
    const db = await openDb();
    const items = (await getAll(db, 'stock_entries'))
      .filter(x => !x.is_archived && Number(x.quantity_current || 0) > 0)
      .map(item => ({...item, priority_level: calcPriority(item)}))
      .sort((a,b) => {
        const pr = ['expired','critical','high','normal','low'];
        return pr.indexOf(a.priority_level) - pr.indexOf(b.priority_level) || String(a.food_name_snapshot).localeCompare(String(b.food_name_snapshot), 'sr');
      });
    db.close();
    return items;
  }

  async function listMovements(limit){
    const db = await openDb();
    const items = (await getAll(db, 'inventory_movements'))
      .sort((a,b) => String(b.movement_date).localeCompare(String(a.movement_date)))
      .slice(0, limit || 200);
    db.close();
    return items;
  }

  async function getSummary(){
    const [stock, locations, movements, foods] = await Promise.all([listActiveStock(), listLocations(), listMovements(999), listFoodSuggestions(9999)]);
    const urgent = stock.filter(x => ['expired','critical','high'].includes(x.priority_level));
    const leftovers = stock.filter(x => x.status === 'leftover');
    const expired = stock.filter(x => x.priority_level === 'expired');
    const nutriCatalog = foods.filter(x => x.source_catalog === 'NUTRI_STL').length;
    return {
      activeStock: stock.length,
      urgent: urgent.length,
      leftovers: leftovers.length,
      expired: expired.length,
      locations: locations.length,
      movements: movements.length,
      nutriCatalog
    };
  }

  function buildSuggestion(title, reason, items, action){
    return { title, reason, items, action };
  }

  async function savePlan(plan){
    const db = await openDb();
    const item = {
      id: makeId('plan'),
      title: plan.title || ('Iz frižidera ' + new Date().toLocaleString('sr-RS')),
      plan_type: plan.plan_type || 'fridge-mvp',
      days_count: Number(plan.days_count || 1),
      generated_from_mode: plan.generated_from_mode || 'stock_entries',
      created_at: isoNow(),
      source_snapshot_ref: null,
      summary_json: plan,
      notes: 'Sačuvan iz MVP generatora.'
    };
    await putOne(db, 'menu_plans_local', item);
    db.close();
    return item;
  }

  async function generateFridgePlan(horizon){
    const stock = await listActiveStock();
    const days = Number(horizon || 1);
    const priorityItems = stock.slice(0, 10);
    const leftovers = stock.filter(x => x.status === 'leftover').slice(0, 3);
    const opened = stock.filter(x => x.status === 'opened').slice(0, 4);
    const vegetables = stock.filter(x => x.category_id === 'vegetables').slice(0, 6);
    const proteins = stock.filter(x => ['meat','fish','eggs','dairy','legumes'].includes(x.category_id)).slice(0, 6);
    const starch = stock.filter(x => ['grains','pasta_rice','bread_bakery'].includes(x.category_id)).slice(0, 6);
    const fruits = stock.filter(x => x.category_id === 'fruits').slice(0, 4);

    const suggestions = [];
    if(leftovers.length){
      suggestions.push(buildSuggestion(
        'Prvo potroši ostatke',
        'Ostaci gotovih jela imaju najveći prioritet u FEFO logici.',
        leftovers.map(x => x.food_name_snapshot),
        'Planiraj prvi obrok iz ostataka i oslobodi frižider.'
      ));
    }
    if(opened.length){
      suggestions.push(buildSuggestion(
        'Otvorena pakovanja imaju prednost',
        'Otvorena pakovanja i visoko kvarljive stavke treba zatvarati pre novih otvaranja.',
        opened.map(x => x.food_name_snapshot),
        'Uključi ih u doručak, sendvič ili brzu večeru.'
      ));
    }
    if(vegetables.length && proteins.length){
      suggestions.push(buildSuggestion(
        'Tiganj / wok / varivo',
        'Imaš kombinaciju povrća i proteinske osnove.',
        [...vegetables.slice(0,3).map(x=>x.food_name_snapshot), ...proteins.slice(0,2).map(x=>x.food_name_snapshot)],
        'Jedan lonac ili jedan tiganj je najbrži način za kontrolisano trošenje zaliha.'
      ));
    }
    if(vegetables.length && starch.length){
      suggestions.push(buildSuggestion(
        'Supa, čorba ili poslužavnik iz rerne',
        'Povrće + skrob daju dobar temelj za 1–3 dana.',
        [...vegetables.slice(0,3).map(x=>x.food_name_snapshot), ...starch.slice(0,2).map(x=>x.food_name_snapshot)],
        'Dobro za dan, dva ili zamrzavanje porcija.'
      ));
    }
    if(fruits.length && proteins.some(x => ['dairy'].includes(x.category_id))){
      suggestions.push(buildSuggestion(
        'Brzi doručak / užina',
        'Voće i mlečni proizvodi mogu zatvoriti doručak bez dodatne nabavke.',
        [...fruits.slice(0,2).map(x=>x.food_name_snapshot), ...proteins.filter(x=>x.category_id==='dairy').slice(0,2).map(x=>x.food_name_snapshot)],
        'Potroši najmekše voće i otvorene mlečne proizvode prvo.'
      ));
    }
    if(!suggestions.length){
      suggestions.push(buildSuggestion(
        'Ručni pregled prioritetnih stavki',
        'Nema dovoljno kombinacija za automatski obrazac, ali prioritet lista je spremna.',
        priorityItems.map(x => x.food_name_snapshot),
        'Odaberi 3–5 najhitnijih i složi 1 obrok ili 1 dan ručno.'
      ));
    }

    const shoppingHints = [];
    if(days >= 3 && proteins.length < 2) shoppingHints.push('Za više dana planiraj dopunu proteinske osnove.');
    if(days >= 3 && vegetables.length < 3) shoppingHints.push('Povrće je tanko za višednevni plan — dopuni 2–3 osnovne stavke.');
    if(days >= 7 && starch.length < 2) shoppingHints.push('Za 7+ dana nedostaje stabilna baza: pirinač, testenina, krompir ili hleb.');

    return {
      horizon_label: days === 1 ? '1 obrok / 1 dan' : (days + ' dana'),
      days_count: days,
      generated_at: isoNow(),
      priority_items: priorityItems,
      suggestions,
      shopping_hints: shoppingHints
    };
  }


  async function addPurchaseBatch(payload){
    const db = await openDb();
    const items = Array.isArray(payload?.items) ? payload.items.filter(x => x && (x.food_item_id || x.food_name) && Number(x.quantity || 0) > 0) : [];
    if(!items.length){
      db.close();
      throw new Error('Dodaj bar jednu stavku nabavke.');
    }

    const locations = await getAll(db, 'storage_locations');
    const purchaseDate = payload.purchase_date || isoNow().slice(0,10);
    const log = {
      id: makeId('purchase'),
      purchase_date: purchaseDate,
      store_name: payload.store_name || 'Lokalna nabavka',
      document_type: payload.document_type || 'receipt',
      document_ref: payload.document_ref || '',
      total_amount: payload.total_amount === '' || payload.total_amount === null || payload.total_amount === undefined ? null : Number(payload.total_amount),
      currency: payload.currency || 'RSD',
      input_method: payload.input_method || 'manual_mvp',
      receipt_image_refs: [],
      qr_payload: payload.qr_payload || '',
      notes: payload.notes || ''
    };
    await putOne(db, 'purchase_logs', log);

    const createdEntries = [];
    for(const rawItem of items){
      const foodItem = await findFoodItem(db, { food_item_id: rawItem.food_item_id, food_name: rawItem.food_name });
      if(!foodItem) continue;
      const location = locations.find(x => x.id === rawItem.assigned_location_id || x.id === rawItem.location_id) || locations[0] || null;
      const categoryId = foodItem.category_id || rawItem.category_id || 'other';
      const status = rawItem.status || 'sealed';
      const unit = rawItem.unit || foodItem.default_unit || 'g';
      const qty = Number(rawItem.quantity || 0);
      if(!(qty > 0)) continue;

      const pli = {
        id: makeId('pli'),
        purchase_log_id: log.id,
        food_item_id: foodItem.id,
        raw_label: rawItem.raw_label || rawItem.food_name || foodItem.name,
        normalized_name: normalizeText(rawItem.food_name || foodItem.name),
        quantity: qty,
        unit,
        price: rawItem.price === '' || rawItem.price === null || rawItem.price === undefined ? null : Number(rawItem.price),
        assigned_location_id: location ? location.id : null,
        mapped_confidence: foodItem.id === rawItem.food_item_id ? 1 : 0.95,
        notes: rawItem.notes || ''
      };
      await putOne(db, 'purchase_log_items', pli);

      const entry = {
        id: makeId('entry'),
        food_item_id: foodItem.id,
        food_name_snapshot: foodItem.name,
        location_id: location ? location.id : null,
        location_name_snapshot: location ? location.name : '',
        quantity_current: qty,
        unit,
        status,
        source_type: 'purchase',
        purchase_date: purchaseDate,
        entry_date: payload.entry_date || purchaseDate,
        opened_date: rawItem.opened_date || null,
        best_before_date: rawItem.best_before_date || null,
        expiry_date: rawItem.expiry_date || null,
        priority_level: calcPriority({
          status,
          best_before_date: rawItem.best_before_date || null,
          expiry_date: rawItem.expiry_date || null,
          perishable_level: inferPerishableLevel(categoryId, status)
        }),
        batch_label: rawItem.batch_label || '',
        notes: rawItem.notes || '',
        category_id: categoryId,
        perishable_level: inferPerishableLevel(categoryId, status),
        is_archived: false,
        source_catalog: foodItem.source_catalog || null,
        nutri_ref_id: foodItem.nutri_ref_id || null,
        nutri_group: foodItem.nutri_group || null,
        nutri_entry_snapshot: buildNutriEntrySnapshot(foodItem)
      };
      await putOne(db, 'stock_entries', entry);
      await putOne(db, 'inventory_movements', {
        id: makeId('mov'),
        entry_id: entry.id,
        movement_type: 'purchase_in',
        movement_date: isoNow(),
        quantity_delta: qty,
        unit: entry.unit,
        reason: 'Nabavka / ulaz robe',
        source_ref_type: 'purchase_log',
        source_ref_id: log.id,
        from_location_id: null,
        to_location_id: entry.location_id,
        notes: `${entry.food_name_snapshot} • ${log.store_name}`
      });
      createdEntries.push(entry);
    }
    db.close();
    return { log, entries: createdEntries };
  }

  async function listPurchaseLogs(limit){
    const db = await openDb();
    const logs = (await getAll(db, 'purchase_logs'))
      .sort((a,b) => String(b.purchase_date || '').localeCompare(String(a.purchase_date || '')) || String(b.id).localeCompare(String(a.id)))
      .slice(0, limit || 100);
    const items = await getAll(db, 'purchase_log_items');
    db.close();
    return logs.map(log => {
      const its = items.filter(x => x.purchase_log_id === log.id);
      const sum = its.reduce((acc, x) => acc + Number(x.price || 0), 0);
      return {
        ...log,
        items_count: its.length,
        computed_total: sum || log.total_amount || null,
        item_labels: its.slice(0,5).map(x => x.raw_label || x.normalized_name || x.food_item_id)
      };
    });
  }

  async function exportAll(){
    const db = await openDb();
    const payload = {
      exported_at: isoNow(),
      db_name: DB_NAME,
      version: VERSION,
      stores: {}
    };
    for(const name of STORE_NAMES){
      payload.stores[name] = await getAll(db, name);
    }
    db.close();
    return payload;
  }

  async function importAll(payload, mode){
    const db = await openDb();
    const tx = db.transaction(STORE_NAMES, 'readwrite');
    for(const name of STORE_NAMES){
      const store = tx.objectStore(name);
      if(mode === 'replace') store.clear();
      const items = Array.isArray(payload?.stores?.[name]) ? payload.stores[name] : [];
      items.forEach(item => store.put(item));
    }
    await txDone(tx);
    db.close();
    await seedIfNeeded();
  }

  function downloadJson(data, filename){
    const blob = new Blob([JSON.stringify(data, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }


  function statusLabel(status){
    return STATUS_LABELS[status] || status || '—';
  }

  function renderStatusChip(status){
    const klass = ({sealed:'ok', opened:'warn', leftover:'warn', frozen:'', consumed:'ok', waste:'bad'})[status] || '';
    const klassText = klass ? ` ${klass}` : '';
    return `<span class="kzh-chip${klassText}">${escapeHtml(statusLabel(status))}</span>`;
  }

  function movementTypeLabel(type){
    return MOVEMENT_TYPE_LABELS[type] || type || '—';
  }

  function renderPriorityChip(priority){
    return `<span class="kzh-priority ${priority}">${priorityLabel(priority)}</span>`;
  }

  function renderNutriPreview(foodItem){
    if(!foodItem){
      return '<div class="kzh-empty">Izaberi namirnicu iz NutriTable liste. Kategorija, podrazumevana jedinica i Nutri snapshot će se povući automatski.</div>';
    }
    const per = getNutriPer100g(foodItem.nutri_snapshot);
    const gi = foodItem?.nutri_snapshot?.gi;
    const tags = Array.isArray(foodItem?.nutri_snapshot?.tags) ? foodItem.nutri_snapshot.tags.slice(0,6) : [];
    const desc = foodItem?.nutri_snapshot?.description || '';
    const descText = typeof desc === 'string' ? desc : (desc?.sr || desc?.text || '');
    return `
      <div class="kzh-preview-grid">
        <div><b>Naziv</b><div>${escapeHtml(foodItem.name)}</div></div>
        <div><b>Nutri grupa</b><div>${escapeHtml(foodItem.nutri_group || '—')}</div></div>
        <div><b>Kategorija za zalihe</b><div>${escapeHtml(foodItem.category_id || '—')}</div></div>
        <div><b>Podrazumevana jedinica</b><div>${escapeHtml(foodItem.default_unit || '—')}</div></div>
        <div><b>GI</b><div>${gi ?? '—'}</div></div>
        <div><b>kcal / 100g</b><div>${per.kcal ?? '—'}</div></div>
      </div>
      <div class="kzh-inline" style="margin-top:8px;gap:6px;">
        <span class="kzh-chip ok">Izvor: NutriTable / NUTRI_STL</span>
        ${foodItem.nutri_ref_id ? `<span class="kzh-chip">Ref: ${escapeHtml(foodItem.nutri_ref_id)}</span>` : ''}
        ${tags.map(tag => `<span class="kzh-chip">${escapeHtml(tag)}</span>`).join('')}
      </div>
      ${descText ? `<p class="kzh-mini" style="margin-top:8px;">${escapeHtml(descText).slice(0,280)}</p>` : ''}
      <p class="kzh-footer-note">Prilikom unosa u Kućne zalihe čuva se i lokalni snapshot Nutri podatka za izabranu namirnicu.</p>
    `;
  }

  async function initCommon(){
    await seedIfNeeded();
    const btn = document.querySelector('[data-kzh-menu-toggle]');
    if(btn){
      btn.addEventListener('click', () => {
        const drawer = document.querySelector('[data-kzh-drawer]');
        if(drawer) drawer.classList.toggle('open');
      });
    }
    const versionEls = document.querySelectorAll('[data-kzh-version]');
    versionEls.forEach(el => el.textContent = VERSION);
  }

  window.PHKZ = {
    VERSION,
    initCommon,
    seedIfNeeded,
    listLocations,
    listCategories,
    listUnits,
    listFoodSuggestions,
    getFoodItemDetails,
    addLocation,
    addStockEntry,
    listActiveStock,
    listMovements,
    getSummary,
    updateEntryTerminal,
    generateFridgePlan,
    savePlan,
    addPurchaseBatch,
    listPurchaseLogs,
    exportAll,
    importAll,
    downloadJson,
    formatDate,
    renderPriorityChip,
    priorityLabel,
    statusLabel,
    renderStatusChip,
    movementTypeLabel,
    renderNutriPreview,
    foodSelectionLabel
  };
})();
