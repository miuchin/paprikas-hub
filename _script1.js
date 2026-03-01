ncoming = out;
      if (!out.length && bad){ console.warn('NDJSON parse: bad lines', bad); }

    } else {
      // prvo pokušaj normalan JSON
      try{
        const obj = JSON.parse(text);
        if (Array.isArray(obj)) incoming = obj;
        else if (obj && Array.isArray(obj.recipes)) incoming = obj.recipes;
        else if (obj && Array.isArray(obj.data)) incoming = obj.data;
        else incoming = [];
      }catch(parseErr){
        // fallback: autodetekcija NDJSON čak i ako je ekstenzija .json
        const {out, bad} = parseNdjson(text);
        if (out && out.length){
          
      incoming = out;
      if (!out.length && bad){ console.warn('NDJSON parse: bad lines', bad); }

      if (!out.length && bad){ console.warn('NDJSON parse: bad lines', bad); }

        } else {
          throw parseErr;
        }
      }
    }
  }catch(e){
    alert("Ne mogu da pročitam fajl. Podržano: JSON array, {recipes:[...]}, {data:[...]}, i NDJSON/JSONL (1 recept po liniji).");
    return;
  }

  const normalized = incoming.map(phRecipesNormalizeOne).filter(Boolean);
  if (!normalized.length){
    alert("Nema važećih recepata u fajlu. Ako je ovo NDJSON/JSONL, proveri da je 1 recept = 1 linija. Savet: probaj Export→NDJSON ili pošalji fajl kao JSON array.");
    return;
  }
  const curr = phRecipesLoadUser();
  const merged = phRecipesMergeUnique(curr, normalized);
  phRecipesSaveUser(merged);
  phRecipesRender();
  alert(`✅ Importovano: ${normalized.length} (ukupno tvojih: ${merged.length}).`);
}

function phRecipesExport(){
  const includeAll = !!(document.getElementById("phRecipesExportAll") && document.getElementById("phRecipesExportAll").checked);
  const user = phRecipesLoadUser();
  const base = includeAll ? Object.values(PH_RECIPES.baseById||{}) : [];
  const out = {
    app: "Paprikas Hub",
    kind: "recipes-export",
    version: "v1",
    exported_utc: new Date().toISOString(),
    include_base: includeAll,
    recipes: includeAll ? phRecipesMergeUnique(base, user) : user
  };
  downloadTextFile(`paprikas-recipes-${fileStamp()}.json`, JSON.stringify(out, null, 2), "application/json");
}