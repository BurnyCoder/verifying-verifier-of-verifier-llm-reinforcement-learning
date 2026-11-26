// The same public renderer consumes immutable Pages data or the local live endpoint.
const byId = id => document.getElementById(id);
let study;
const pct = n => n == null ? "—" : (100*n).toFixed(1)+"%";
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
  for(const name of ["examples","evidence","curve"]) byId(name).replaceChildren();
  byId("pair").textContent = "";
  byId("training").textContent = "";
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
  byId("training").textContent="Groups with identical rewards "+r.zero_groups+" / "+r.groups+". Development reviews fixed "+r.fixed+" verdicts and introduced "+r.harmed+" errors across "+r.dev_n+" traces.";
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
    byId("progress").textContent=study.runs.filter(r=>r.updates != null).length+" of "+study.planned+" training blocks completed. "+(study.sealed?"Checkpoint manifest sealed.":"Final test sealed during development.");
    byId("results").replaceChildren();
    for (const r of study.runs) row(byId("results"),[r.name,r.role,r.updates,pct(r.dev),r.dev_n,pct(r.test),r.test_n]);
    const current=byId("run").value;
    byId("run").replaceChildren(...study.runs.map(r=>new Option(r.name,r.name)));
    if (study.runs.some(r=>r.name===current)) byId("run").value=current;
    showRun();
  } catch(e) {byId("primary").textContent="Could not read study observations. "+e.message;}
}
byId("run").addEventListener("change",showRun);
byId("out").addEventListener("change",showRun);
update();
if (live) setInterval(update,15000);
