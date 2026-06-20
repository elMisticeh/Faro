// scripts/colonia_match.test.js — valida devColoniaMatcher (mapa Desarrollo MK7/MK8).
// Reimplementa el matcher (mismo patron que margen_desarrollo.test.js).
const assert = require('assert');

function devColoniaMatcher(rows){
  const deac = s => (s||'').normalize('NFKD').replace(/[̀-ͯ]/g,'');
  const norm = s => deac(s).toLowerCase().replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
  const STOP = /\b(residencial|fraccionamiento|fracc|frac|colonia|col|privada|privadas|priv|cerrada|cerradas|sector|etapa|etepa|seccion|secc|ampliacion|ampl|conjunto|primera|segunda|tercera|cuarta|quinta|sexta|septima|octava|1ra|2da|3ra|4ta|5ta)\b/g;
  const ROM  = /\b([ivx]+|[0-9]+a?)\b\.?\s*$/;
  const clean = s => { let t = norm(s).replace(STOP,' ').replace(/\s+/g,' ').trim();
    for (let i=0;i<3;i++) t = t.replace(ROM,'').trim(); return t; };
  const ART = new Set(['de','del','la','el','los','las']);
  const loose = k => k.split(' ').filter(t => t && !ART.has(t)).join(' ');
  const tokN  = s => s ? s.split(' ').filter(Boolean).length : 0;
  const has   = (hay, needle) => (' '+hay+' ').includes(' '+needle+' ');
  const BLOCK = new Set(['torreon','la rosita','centro','torreon centro']);
  const rowKeys = (rows||[]).map(r => { const key = clean(r.colonia);
      return { r, exact: norm(r.colonia), key, loose: loose(key) }; })
    .filter(x => x.key.length >= 4 && !BLOCK.has(x.key));
  return function(fname){
    const fe = norm(fname), fk = clean(fname), fl = loose(fk);
    let best = null, bestLen = -1;
    for (const x of rowKeys){
      const hit = (x.exact===fe) || (x.key===fk) || (fk.length>=4 && has(fk, x.key))
        || (tokN(x.loose)>=2 && (x.loose===fl || has(fl, x.loose)));
      if (hit && x.key.length > bestLen){ best = x.r; bestLen = x.key.length; }
    }
    return best;
  };
}

const rows = [
  {colonia:'Las Villas'}, {colonia:'Las Acacias'}, {colonia:'El Cardenchal'},
  {colonia:'Las Trojes'}, {colonia:'Hacienda San José'}, {colonia:'San Isidro'},
  {colonia:'La Unión'}, {colonia:'Torreón'}, {colonia:'Ampliación la Rosita'},
  {colonia:'Hacienda del Rosario'}, {colonia:'Quintas San Isidro'},
];
const m = devColoniaMatcher(rows);
const col = x => { const r = m(x); return r ? r.colonia : null; };

// Fragmentacion por etapa -> colonia base
assert.strictEqual(col('RESIDENCIAL LAS VILLAS ETAPA XIII'), 'Las Villas', 'etapa romana');
assert.strictEqual(col('RESIDENCIAL LAS VILLAS 7A. ETAPA'), 'Las Villas', 'etapa 7a');
assert.strictEqual(col('RESIDENCIAL LAS TROJES II ETAPA'), 'Las Trojes', 'trojes etapa');
assert.strictEqual(col('RESIDENCIAL EL CARDENCHAL'), 'El Cardenchal', 'prefijo residencial');
assert.strictEqual(col('RESIDENCIAL HACIENDA SAN JOSE'), 'Hacienda San José', 'sin acento + residencial');
// Variante "del" vs "el" + prefijo/sufijo (caso Hacienda del Rosario)
assert.strictEqual(col('RESIDENCIAL HACIENDA EL ROSARIO'), 'Hacienda del Rosario', 'del<->el clave suelta');
assert.strictEqual(col('HACIENDA EL ROSARIO TERCERA ETAPA'), 'Hacienda del Rosario', 'el + ordinal + etapa');
// La guarda de >=2 tokens evita que "Las Villas" (loose "villas") agarre de mas
assert.strictEqual(col('VILLAS DE LA HUERTA'), null, 'villas 1-token no debe colapsar');
assert.strictEqual(col('FRANCISCO VILLA'), null, 'villa singular tampoco');
// Acentos
assert.strictEqual(col('EJIDO LA UNION'), 'La Unión', 'la union via substring');
// Especificidad: gana el alias mas largo
assert.strictEqual(col('QUINTAS SAN ISIDRO'), 'Quintas San Isidro', 'gana el mas especifico, no San Isidro');
assert.strictEqual(col('SAN ISIDRO'), 'San Isidro', 'exacto corto');
// Blocklist: genericos NO pintan
assert.strictEqual(col('PANTEON TORREON'), null, 'Torreon bloqueado');
assert.strictEqual(col('TORREON VIEJO'), null, 'Torreon bloqueado 2');
assert.strictEqual(col('RINCON LA ROSITA'), null, 'La Rosita bloqueada');
// Sin relacion -> null
assert.strictEqual(col('FRANCISCO VILLA'), null, 'no es Las Villas');
assert.strictEqual(col('VILLAS DE LA HUERTA'), null, 'no es Las Villas');
// Sin poligono propio: el nombre no aparece en ningun feature -> el matcher
// simplemente no lo asignara (se prueba arriba con features reales).

console.log('OK — devColoniaMatcher: fragmentacion, acentos, especificidad y blocklist validados');
