// The same public renderer consumes immutable Pages data or the local live endpoint.
const byId = id => document.getElementById(id);
let study;
const pct = n => n == null ? "—" : (100*n).toFixed(1)+"%";
function drawTrend(groups) {
  const chart = byId("trend");
  chart.hidden = !groups.length;
  if (!groups.length) return;
  const width = Math.max(270,chart.getBoundingClientRect().width), height = 220;
  const resolution = window.devicePixelRatio || 1;
  chart.width = Math.round(width*resolution); chart.height = Math.round(height*resolution);
  chart.style.height = height+"px";
  const ctx = chart.getContext("2d");
  ctx.scale(resolution,resolution);
  const left = 64, right = width-22, top = 36, bottom = height-32;
  const last = Math.max(2,groups.at(-1).step);
  const x = step => left+(step-1)*(right-left)/(last-1);
  const y = value => bottom-value*(bottom-top);
  ctx.clearRect(0,0,width,height);
  ctx.font = "14px system-ui";
  for (const value of [0,.5,1]) {
    ctx.strokeStyle = "#c5d3cf";
    ctx.beginPath(); ctx.moveTo(left,y(value)); ctx.lineTo(right,y(value)); ctx.stroke();
    ctx.fillStyle = "#375a59"; ctx.fillText((value*100)+"%",5,y(value)+4);
  }
  for (const [field,label,color,dash,legendX] of [
    ["reward","Assigned reward","#17665b",[],left],["exact","Exact accuracy","#ac4f2c",[5,4],left+133]]) {
    ctx.strokeStyle = ctx.fillStyle = color;
    ctx.lineWidth = 2; ctx.setLineDash(dash); ctx.beginPath();
    groups.forEach((g,i) => i ? ctx.lineTo(x(g.step),y(g[field])) : ctx.moveTo(x(g.step),y(g[field])));
    ctx.stroke();
    const tail=groups.at(-1);
    ctx.beginPath(); ctx.arc(x(tail.step),y(tail[field]),3,0,2*Math.PI); ctx.fill();
    ctx.fillText(label,legendX,19);
  }
  ctx.setLineDash([]); ctx.fillStyle="#375a59";
  ctx.fillText("Update 1",left,height-5); ctx.textAlign="right";
  ctx.fillText("Update "+groups.at(-1).step,right,height-5); ctx.textAlign="left";
}
function row(body, fields) {
  const tr = document.createElement("tr");
  for (const field of fields) {
    const td = document.createElement("td");
    td.textContent = field ?? "—";
    tr.append(td);
  }
  body.append(tr);
}
function exampleCard(title, lines, error) {
  const card = document.createElement("article");
  if (error) card.classList.add("error");
  const heading = document.createElement("h3");
  heading.textContent = title;
  const record = document.createElement("pre");
  record.textContent = lines.join("\n");
  card.append(heading, record);
  return card;
}
function showRun() {
  const r = study?.runs.find(item => item.name === byId("run").value);
  for(const name of ["examples","evidence","curve","replay"]) byId(name).replaceChildren();
  byId("pair").textContent = "";
  byId("training").textContent = "";
  byId("probe").textContent = "";
  drawTrend(r?.curves ?? []);
  if (!r) {
    byId("examples").textContent = "Examples will appear after the first development evaluation.";
    return;
  }
  const chosen = r.examples.filter(e => byId("out").value === "all" || String(e.correct) === byId("out").value);
  for (const e of chosen) byId("examples").append(exampleCard(e.correct ? "Correct trace" : "Incorrect trace",
    [...e.problem,"Solver  "+e.trace,"Exact  "+e.expected_values.join(","),...e.reports.map((j,i)=>"Judge "+(i+1)+"  "+j)],!e.correct));
  if (!chosen.length) byId("examples").textContent="No recorded example matches this selection.";
  byId("pair").textContent = r.twins_n ? "Both twins correct with evidence "+pct(r.twins)+", with evidence masked "+pct(r.masked)+". Pairs scored "+r.twins_n+" ("+r.twin_split+")." : "Paired reviews are pending.";
  if (r.paired_example) {
    const p = r.paired_example;
    byId("evidence").append(exampleCard(p.expression,["Solver  "+p.trace,"Judge 1  "+p.first,
      ...p.reviews.map((v,i)=>"Judge 2  "+v+"\nJudge 3  "+p.visible[i]+"\nExpected Judge 3  "+p.labels[i].join(","))],false));
  }
  for (const [phase,methods] of [["Development",r.replay],["Held out",r.test_replay]]) {
    for (const m of methods ?? []) if (m.n) row(byId("replay"),[phase,m.method,pct(m.agreement),
      m.false_accept+"/"+(m.invalid ?? "—"),m.false_reject+"/"+(m.valid ?? "—"),(m.malformed ?? "—")+"/"+(m.reports ?? "—")]);
  }
  const findings=[];
  if (r.groups) findings.push("Groups with identical rewards "+r.zero_groups+" / "+r.groups+".");
  if (r.dev_n) findings.push("Across "+r.dev_n+" development traces, Judge 3 corrected "+r.fixed+" verdicts and introduced "+r.harmed+" errors.");
  byId("training").textContent=findings.join(" ");
  const probe=r.logs.filter(e=>e.development_accuracy!=null).at(-1);
  if (probe) byId("probe").textContent="Latest greedy development check at update "+probe.step+" · "+pct(probe.development_accuracy)+" complete-trace accuracy on "+probe.development_n+" problems.";
  for (const step of r.curves.slice(-20).reverse()) row(byId("curve"),[step.step,pct(step.reward),pct(step.exact)]);
}
const live = ["127.0.0.1","localhost","[::1]"].includes(location.hostname);
async function update() {
  try {
    const response = await fetch(live ? "/live.json" : "assets/study.json",{cache:"no-store"});
    if (!response.ok) throw Error(response.statusText);
    study = await response.json();
    const p=study.primary;
    byId("primary").textContent=p.delta == null ? "Awaiting matched final checkpoints for all registered seeds." : "Three judges minus two: "+(p.delta*100).toFixed(2)+" points. 95% interval "+p.ci.map(x=>(100*x).toFixed(2)).join(" to ")+". Decision: "+p.status+".";
    byId("progress").textContent=study.runs.filter(r=>r.updates != null && !r.diagnostic).length+" of "+study.planned+" registered training blocks completed. "+(study.sealed?"Checkpoint manifest sealed.":"Final test sealed during development.");
    const cal=study.learnability;
    byId("calibration").replaceChildren();
    byId("readiness").textContent=cal?.screen?.selected ? "Selected "+cal.screen.selected.family+" with "+cal.screen.selected.style+" prompts." :
      cal?.screen ? "No configuration qualified under the registered rule." : "The frozen-model difficulty screen is pending.";
    for (const c of cal?.screen?.cells ?? []) row(byId("calibration"),[c.family,c.style,pct(c.parsed),pct(c.sampled_exact),pct(c.greedy_exact),c.mixed_groups+" / "+c.problems]);
    const vals=Object.entries(cal?.evaluations ?? {}).filter(([,v])=>v).map(([k,v])=>k+" "+v.correct+"/"+v.n);
    byId("learned").textContent=cal?.learning ? "Learning criterion "+(cal.learning.demonstrated?"met. ":"unmet. ")+vals.join(" · ") :
      vals.length ? "Fresh validation outcomes · "+vals.join(" · ") : "The positive-control test compares exact-reward training with the starting solver and shuffled rewards.";
    byId("results").replaceChildren();
    for (const r of study.runs) row(byId("results"),[r.name,r.role,r.updates,pct(r.dev),r.dev_n,pct(r.test),r.test_n]);
    const current=byId("run").value || study.runs.find(r=>r.name!=="base" && r.updates==null)?.name;
    byId("run").replaceChildren(...study.runs.map(r=>new Option(r.name,r.name)));
    if (study.runs.some(r=>r.name===current)) byId("run").value=current;
    showRun();
  } catch(e) {byId("primary").textContent="Could not read study observations. "+e.message;}
}
byId("run").addEventListener("change",showRun);
byId("out").addEventListener("change",showRun);
window.addEventListener("resize",()=>drawTrend(study?.runs.find(r=>r.name===byId("run").value)?.curves ?? []));
update();
if (live) setInterval(update,15000);
