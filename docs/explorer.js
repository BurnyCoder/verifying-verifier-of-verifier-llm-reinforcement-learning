// The same public renderer consumes immutable Pages data or the local live endpoint.
const byId = id => document.getElementById(id);
let study;
let renderedComparisons;
const pct = n => n == null ? "—" : (100*n).toFixed(1)+"%";
function drawTrend(groups, chart = byId("trend")) {
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
function showMatched(grids) {
  const section=byId("matched-section"), target=byId("matched-tables");
  const revision=JSON.stringify(grids);
  if (renderedComparisons===revision) return;
  renderedComparisons=revision;
  const openPhases=new Set(Array.from(target.querySelectorAll("details[open]"),item=>item.dataset.phase));
  target.replaceChildren();
  section.hidden=grids.length===0;
  for (const grid of [...grids].reverse()) {
    const split=grid.phase==="development" ? "Development" : "Held-out";
    for (const [label,records] of [["solver accuracy",grid.solver],["judge verdict accuracy",grid.judge]]) {
      const wrapper=document.createElement("div"), table=document.createElement("table");
      wrapper.className="scroll";
      table.createCaption().textContent=split+" "+label+" · seed 17";
      const header=table.createTHead().insertRow();
      for (const label of ["Training condition","One judge","Two · J2 checks J1","Three · J3 checks J2"]) {
        const cell=document.createElement("th");
        cell.scope="col"; cell.textContent=label; header.append(cell);
      }
      const body=table.createTBody();
      for (const fields of records) row(body,fields);
      wrapper.append(table); target.append(wrapper);
      if (label==="solver accuracy" && grid.solver_note) {
        const note=document.createElement("p"); note.textContent=grid.solver_note; target.append(note);
      }
    }
    if (grid.judge_note) {
      const note=document.createElement("p"); note.textContent=grid.judge_note; target.append(note);
    }
    if (grid.frozen_changes?.length) {
      const details=document.createElement("details"), summary=document.createElement("summary");
      details.dataset.phase=grid.phase;
      details.open=openPhases.has(grid.phase);
      summary.textContent="Every changed frozen-judge verdict on the starting solver";
      const wrap=document.createElement("div"), table=document.createElement("table");
      wrap.className="scroll";
      const header=table.createTHead().insertRow();
      for (const label of ["Problem","Solver wrote","Exact steps","Judge 2","Judge 3","Effect"]) {
        const cell=document.createElement("th"); cell.scope="col"; cell.textContent=label; header.append(cell);
      }
      const body=table.createTBody();
      for (const record of grid.frozen_changes) {
        const verdict=level=>(record.verdicts[level] ? "Accept" : "Reject")+" · "+record.reports[level];
        row(body,[record.expression,record.trace,record.expected_values.join(","),verdict(1),verdict(2),
                  Boolean(record.verdicts[2])===Boolean(record.correct) ? "Fixed a grading error" : "Introduced a grading error"]);
      }
      wrap.append(table); details.append(summary,wrap); target.append(details);
    }
  }
}
function showInventory() {
  const entries = study?.inventory ?? [];
  const filter = byId("inventory-phase");
  for (const phase of new Set(entries.map(r => r.group))) {
    if (![...filter.options].some(option => option.value === phase)) filter.add(new Option(phase, phase));
  }
  const body = byId("inventory");
  body.replaceChildren();
  for (const record of entries.filter(r => !filter.value || r.group === filter.value)) {
    row(body, [record.id, record.treatment, record.status, record.result, record.held_out]);
    if (record.evidence) {
      const link = document.createElement("a");
      link.href = record.evidence;
      link.textContent = record.id;
      body.lastElementChild.firstElementChild.replaceChildren(link);
    }
  }
}
function showOnline() {
  const fits=study?.solver_fit ?? [], bodyFit=byId("solver-fit-rows");
  byId("solver-fit-section").hidden=!fits.length;
  byId("solver-choice").textContent=study?.solver_fit_assessment ?? "";
  bodyFit.replaceChildren();
  for (const f of fits) row(bodyFit,[f.model,f.precision.toUpperCase(),f.status,f.n ? f.parsed+"/"+f.n : "—",
    f.n ? f.correct+"/"+f.n : "—",f.after_step ? Math.round(f.after_step.solver_peak_mib)+" MiB" : "—"]);
  const online=study?.online_solvers, block=byId("online-section");
  block.hidden=!online?.arms;
  if (block.hidden) return;
  const body=byId("online-scores"), effect=online.comparison?.d3_minus_d2;
  body.replaceChildren();
  row(body,["Starting solver","Evaluated",0,"—","—",online.base.correct+"/"+online.base.n]);
  for (const arm of online.arms) {
    const probe=arm.probes.at(-1), sig=arm.signal;
    row(body,["Judge "+arm.depth,arm.status,arm.updates+"/"+online.plan.updates,sig.groups ? sig.mixed+"/"+sig.groups : "—",
      probe ? Math.round(probe.development_accuracy*probe.development_n)+"/"+probe.development_n+" at step "+probe.step : "—",
      arm.n ? arm.correct+"/"+arm.n : "Pending"]);
  }
  byId("online-result").textContent=effect ? "The accuracy difference on the same development questions (three judges minus two) was "+(effect.delta*100).toFixed(2)+" percentage points (paired 95% interval "+effect.interval.map(x=>(100*x).toFixed(1)).join(" to ")+")." :
    "Fresh seed-17 solver adapters receive the final judge’s verdict. The independent integer checker scores every arithmetic step.";
  const contrasts=online.three_depths?.contrasts, changes=byId("contrast-rows");
  if (contrasts) {
    const arms=online.three_depths.arms, total=arms.reduce((n,a)=>n+a.n,0);
    const agree=arms.reduce((n,a)=>n+(a.unanimous_solution_verdicts ?? 0),0);
    byId("online-result").textContent="The matched solvers trained with one, two and three frozen judges solved "+
      arms.map(a=>a.solver+"/"+a.n).join(", ")+" development problems, respectively. "+
      (arms.every(a=>a.unanimous_solution_verdicts!=null) ? "All three graders agreed on "+agree+"/"+total+" saved answers. " : "")+
      "The one-judge baseline was added after the deeper scores were known. The paired intervals describe these seed-17 checkpoints.";
  }
  byId("online-contrasts").hidden=!contrasts;
  changes.replaceChildren();
  for (const [key,label] of [["one_minus_base","One minus starting solver"],["two_minus_one","Two minus one"],["three_minus_one","Three minus one"],["three_minus_two","Three minus two"]]) {
    const change=contrasts?.[key];
    if (change) row(changes,[label,change.fixed,change.harmed,(100*change.delta).toFixed(2),change.interval.map(x=>(100*x).toFixed(1)).join(" to ")]);
  }
  const selected=online.arms.find(a=>a.depth===Number(byId("online-depth").value)) ?? online.arms[0];
  byId("online-depth").value=selected.depth;
  drawTrend(selected.signal.curves,byId("online-trend"));
  const group=selected.latest_group ?? [];
  byId("online-group").hidden=!group.length;
  const groupRows=byId("group-rows");
  groupRows.replaceChildren();
  if (group.length) {
    byId("group-problem").textContent="Update "+(group[0].step+1)+" · "+group[0].expression+" · "+group.at(-1).time;
    for (const r of group) row(groupRows,[r.answer,r.reports[0],r.reports[1] ?? "—",r.reports[2] ?? "—",r.label,r.reward]);
    byId("online-log").href=live ? "/live/training-log/"+selected.depth :
      "https://huggingface.co/datasets/BurnyCoder/recursive-judge-grpo-study/tree/main/logs/"+selected.name;
  }
  const replays=online.three_depths?.arms ?? online.comparison?.development_replays ?? [];
  byId("online-fixed").hidden=!replays.length;
  const fixed=byId("fixed-rows"), examples=byId("online-examples");
  fixed.replaceChildren(); examples.replaceChildren();
  replays.forEach((r,i)=>row(fixed,["Judge "+(r.depth ?? i+2), ...[r.solver,r.j1_correct,r.j2_correct,r.j3_correct].map(k=>k==null ? "—" : k+"/"+r.n), r.fixed,r.harmed]));
  const allDepths=online.three_depths?.examples;
  for (const ex of allDepths ?? online.comparison?.examples ?? []) {
    const lines=["Exact steps: "+ex.expected.join(", ")];
    ex.traces.forEach((trace,i)=>lines.push("Solver trained with Judge "+(i+(allDepths ? 1 : 2))+" wrote "+JSON.stringify(trace)+
      (ex.correct[i] ? " (correct)" : " (incorrect)"),...ex.reports[i].map((r,j)=>"  Judge "+(j+1)+" wrote "+JSON.stringify(r))));
    examples.append(exampleCard(ex.expression,lines,ex.correct.includes(0)));
  }
}
function showNewJudges() {
  const body = byId("frozen-scores");
  body.replaceChildren();
  const newer = study.newer_judges ?? {};
  const messages = newer.headline ? [newer.headline.replace(/\.$/,"")] : [];
  const examples=byId("frozen-evidence");
  const openKeys=new Set([...examples.querySelectorAll("details[open]")].map(e=>e.dataset.key));
  examples.replaceChildren();
  for (const result of newer.results ?? []) {
    messages.push(result.model+" · "+result.phase+" · "+result.result);
    for (const name of ["balanced","natural"]) {
      const cohort=result.metrics?.[name], twins=result.metrics?.twins;
      if (!cohort?.n) continue;
      row(body,[result.model+" · "+result.phase+" · "+name,...cohort.depths.map(d => d.correct+"/"+cohort.n),
        ...["visible","masked"].map(k => name==="balanced" ? twins[k]+"/"+twins.n : "—"),cohort.fixed+" / "+cohort.harmed]);
    }
    if (result.audit?.examples) {
      const details=document.createElement("details"), summary=document.createElement("summary");
      details.dataset.key=result.key; details.open=openKeys.has(result.key);
      summary.textContent="Evidence examples · "+result.model+" · "+result.phase;
      details.append(summary);
      for (const [outcome,x] of Object.entries(result.audit.examples)) {
        const lines=["Solver "+x.trace,"Judge 1 "+x.first,...x.reviews.map((v,i)=>
          "Judge 2 "+v+"\nJudge 3 "+x.outputs[i]+"\nExpected "+x.expected[i])];
        details.append(exampleCard(x.expression+" · pair "+outcome,lines,outcome==="failed"));
      }
      examples.append(details);
    }
  }
  const chart=byId("frozen-chart");
  const version=(newer.results ?? []).filter(r=>r.metrics).map(r=>r.key).join(",");
  if (version && chart.dataset.version!==version) {
    chart.dataset.version=version;
    chart.onload=()=>{chart.hidden=false;};
    chart.onerror=()=>{chart.hidden=true;delete chart.dataset.version;};
    chart.src="assets/frozen-judge-scores.png?v="+encodeURIComponent(version);
  }
  for (const r of study.inventory ?? []) if (r.id.startsWith("new-judges/") &&
      (r.status.startsWith("Evaluating") || r.status.startsWith("Checking GPU"))) messages.push(r.id+" · "+r.status);
  for (const fit of newer.fit_failures ?? []) messages.push(fit.file+" failed the fit check before inference. "+fit.reason);
  for (const finding of newer.conversions ?? []) messages.push(finding.replace(/\.$/,""));
  if (newer.decision?.result && !study.online_solvers?.plan) messages.push(newer.decision.result);
  for (const [name, estimate] of Object.entries(newer.decision?.estimates ?? {})) {
    const points = x => (100*x).toFixed(2);
    const outcome = name === "twins" ? "Whole evidence pairs" : "Balanced Judge 3 verdicts";
    messages.push(outcome+", candidate minus control, differed by "+points(estimate.delta)+" percentage points on "+estimate.n+
      " paired confirmation problems (95% interval "+points(estimate.ci[0])+" to "+points(estimate.ci[1])+")");
  }
  byId("frozen-status").textContent=messages.join(". ") || "Waiting for the first completed GPU-only evaluation.";
}
byId("inventory-phase").addEventListener("change", showInventory);
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
    byId("progress").textContent=study.runs.filter(r=>r.updates != null && !r.diagnostic && !r.supplemental).length+" of "+study.planned+" registered training blocks completed. "+(study.sealed?"Checkpoint manifest sealed.":"Final test sealed during development.");
    if (study.profile?.family) byId("progress").textContent += " Amended benchmark · "+study.profile.family+" arithmetic with "+study.profile.style+" prompts.";
    showMatched(study.matched_depth ?? []);
    showInventory();
    showOnline();
    showNewJudges();
    const trajectory=byId("depth-trajectory");
    const ready=study.profile?.family==="two-add" && ["d2-17","d3-17"].every(id=>study.runs.some(r=>r.name===id && r.completed_development));
    if (ready && !trajectory.hasAttribute("src")) {
      trajectory.onload=()=>{trajectory.hidden=false;};
      trajectory.src="assets/depth-trajectory.png";
    } else if (!ready) {
      trajectory.removeAttribute("src");
      trajectory.hidden=true;
    }
    const cal=study.learnability;
    byId("calibration").replaceChildren();
    byId("readiness").textContent=cal?.screen?.selected ? "Selected "+cal.screen.selected.family+" with "+cal.screen.selected.style+" prompts." :
      cal?.screen ? "No configuration qualified under the registered rule." : "The frozen-model difficulty screen is pending.";
    for (const c of cal?.screen?.cells ?? []) row(byId("calibration"),[c.family,c.style,pct(c.parsed),pct(c.sampled_exact),pct(c.greedy_exact),c.mixed_groups+" / "+c.problems]);
    if (cal?.confirmation) {
      const c=cal.confirmation.cell;
      byId("readiness").textContent += " Independent confirmation "+(cal.confirmation.confirmed?"passed":"failed")+
        " on "+c.problems+" problems. Greedy complete-trace accuracy "+pct(c.greedy_exact)+
        ", with mixed samples on "+c.mixed_groups+" problems.";
    }
    const vals=Object.entries(cal?.evaluations ?? {}).filter(([,v])=>v).map(([k,v])=>k+" "+v.correct+"/"+v.n);
    byId("learned").textContent=cal?.learning ? "Learning criterion "+(cal.learning.demonstrated?"met. ":"unmet. ")+vals.join(" · ") :
      vals.length ? "Fresh validation outcomes · "+vals.join(" · ") : "The positive-control test compares exact-reward training with the starting solver and shuffled rewards.";
    const arithmetic=cal?.learning?.by_parse?.base?.groups?.find(g=>g.stratum==="Both parsed");
    if (arithmetic) byId("learned").textContent += " Among "+arithmetic.n+" already parseable pairs, training corrected "+arithmetic.gains+" arithmetic traces and broke "+arithmetic.losses+".";
    const chart=byId("validation-chart");
    const version=vals.join("|")+"|"+(cal?.learning?.status ?? "");
    if (vals.length && chart.dataset.version!==version) {
      chart.hidden=true;
      chart.onload=()=>{chart.hidden=false;};
      chart.onerror=()=>{chart.hidden=true; delete chart.dataset.version;};
      chart.dataset.version=version;
      chart.src="assets/learnability.png?v="+encodeURIComponent(version);
    } else if (!vals.length) chart.hidden=true;
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
byId("online-depth").addEventListener("change",showOnline);
window.addEventListener("resize",()=>drawTrend(study?.runs.find(r=>r.name===byId("run").value)?.curves ?? []));
update();
if (live) setInterval(update,15000);
