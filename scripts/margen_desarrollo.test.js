// scripts/margen_desarrollo.test.js — valida la matematica de calcularMargenDesarrollo
const assert = require('assert');

function median(a){ if(!a||!a.length) return null; const x=[...a].sort((p,q)=>p-q); return x[Math.floor(x.length/2)]; }

function calcularMargenDesarrollo(data, costoObra, minMuestras){
  const terrAll = data.filter(d=>d.tipo_inmueble==='terreno'&&d.precio_x_m2_terreno>0).map(d=>d.precio_x_m2_terreno);
  const pm2TerrGlobal = median(terrAll);
  const terrPorColonia = {};
  data.forEach(d=>{ if(d.tipo_inmueble==='terreno'&&d.precio_x_m2_terreno>0&&d.colonia)
    (terrPorColonia[d.colonia]=terrPorColonia[d.colonia]||[]).push(d.precio_x_m2_terreno); });
  const casas = data.filter(d=>d.tipo_inmueble==='casa'&&d.tipo_operacion==='venta'&&d.m2_construccion>0&&d.m2_terreno>0&&d.precio_mxn>0&&d.colonia);
  const porColonia = {};
  casas.forEach(d=>{ (porColonia[d.colonia]=porColonia[d.colonia]||[]).push(d); });
  const out = [];
  Object.entries(porColonia).forEach(([col, arr])=>{
    if(arr.length < minMuestras) return;
    const terrArr = terrPorColonia[col] || [];
    const fallback = terrArr.length < 2;
    const pm2Terr = fallback ? pm2TerrGlobal : median(terrArr);
    if(!pm2Terr) return;
    const residuales = [], tickets = [], m2cs = [];
    arr.forEach(d=>{ const res = (d.precio_mxn - d.m2_terreno*pm2Terr)/d.m2_construccion;
      if(res>0){ residuales.push(res); tickets.push(d.precio_mxn); m2cs.push(d.m2_construccion); } });
    if(!residuales.length) return;
    const residualMediano = median(residuales);
    const m2cMediano = median(m2cs);
    const margenNeto = residualMediano - costoObra;
    const nTerrenos = terrArr.length;
    const confianza = (arr.length>=minMuestras && nTerrenos>=2) ? 'alta'
                    : ((arr.length>=minMuestras || nTerrenos>=2) && !fallback) ? 'media' : 'baja';
    out.push({ colonia:col, nCasas:arr.length, nTerrenos, pm2TerrenoMediana:pm2Terr,
      ticketMediano:median(tickets), m2cMediano, residualMediano, margenNeto,
      margenPorCasa: margenNeto*m2cMediano, confianza });
  });
  return out.sort((a,b)=>b.margenNeto-a.margenNeto);
}

const data = [
  {tipo_inmueble:'terreno',precio_x_m2_terreno:6000,colonia:'A'},
  {tipo_inmueble:'terreno',precio_x_m2_terreno:6000,colonia:'A'},
  ...Array.from({length:4},()=>({tipo_inmueble:'casa',tipo_operacion:'venta',precio_mxn:9000000,m2_terreno:500,m2_construccion:380,colonia:'A'})),
  {tipo_inmueble:'terreno',precio_x_m2_terreno:2000,colonia:'B'},
  {tipo_inmueble:'terreno',precio_x_m2_terreno:2000,colonia:'B'},
  ...Array.from({length:4},()=>({tipo_inmueble:'casa',tipo_operacion:'venta',precio_mxn:3000000,m2_terreno:300,m2_construccion:250,colonia:'B'})),
];

const r = calcularMargenDesarrollo(data, 12000, 4);
assert.strictEqual(r.length, 2, 'deben salir 2 colonias');
assert.strictEqual(r[0].colonia, 'A', 'A debe rankear primero (mayor margen)');
assert.strictEqual(Math.round(r[0].residualMediano), 15789, 'residual A');
assert.strictEqual(Math.round(r[0].margenNeto), 3789, 'margenNeto A = 15789-12000');
assert.strictEqual(r[0].confianza, 'alta', 'A confianza alta (4 casas, 2 terrenos)');
assert.strictEqual(Math.round(r[1].residualMediano), 9600, 'residual B');
console.log('OK — calcularMargenDesarrollo: matematica validada');
