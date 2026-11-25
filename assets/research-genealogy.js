(() => {
  "use strict";
  const DATA_URL = "/metadata/research-genealogy.json";
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
  const dateText = (value) => {
    if (!value) return "Date not recorded";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat(undefined, {dateStyle:"medium",timeStyle:"medium",timeZone:"UTC"}).format(date) + " UTC";
  };
  const link = (url, label) => url
    ? '<a href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(label || url) + '</a>'
    : "";
  const show = (id) => { const node = $(id); if (node) node.hidden = false; };
  const archiveCaptures = (artifact) => {
    const direct = Array.isArray(artifact.archive_captures) ? artifact.archive_captures : [];
    const nested = (artifact.representations || []).flatMap((item) => item.archive_captures || []);
    return [...direct, ...nested];
  };
  const captureEvents = (data) => {
    const events = [];
    (data.milestones || []).forEach((item) => events.push({
      date:item.date,title:item.title,description:item.summary,kind:"Research milestone",
      url:item.source?.url,dateBasis:item.date_basis
    }));
    (data.research_objects || []).forEach((item) => {
      if (item.earliest_archived_capture?.captured_at) events.push({
        date:item.earliest_archived_capture.captured_at,title:item.title,
        description:"Earliest archive observation for this source object.",kind:"Archive observation",
        url:item.earliest_archived_capture.url,dateBasis:"archive capture"
      });
      if (item.first_known_online_by) events.push({
        date:item.first_known_online_by,title:item.title,
        description:item.first_known_online_basis || "First known online date.",
        kind:"First known online",url:item.uri,dateBasis:"first known online by"
      });
    });
    (data.artefacts || []).forEach((item) => archiveCaptures(item).forEach((capture) => {
      if (!capture.captured_at) return;
      events.push({
        date:capture.captured_at,title:item.title,
        description:capture.archive_service + " capture. " + (capture.note || ""),
        kind:"Archive capture",url:capture.url,dateBasis:capture.timestamp_basis
      });
    }));
    return events.sort((a,b)=>new Date(a.date)-new Date(b.date));
  };
  const renderStats = (data) => {
    const captures=(data.artefacts||[]).reduce((sum,item)=>sum+archiveCaptures(item).length,0);
    const timed=(data.artefacts||[]).reduce((sum,item)=>sum+archiveCaptures(item).filter(c=>c.captured_at).length,0);
    const stats=[
      ["Research objects",(data.research_objects||[]).length],
      ["Research processes",(data.research_processes||[]).length],
      ["Artefact records",(data.artefacts||[]).length],
      ["Archive references",captures],
      ["Timestamped captures",timed],
      ["Thematic clusters",(data.research_clusters||[]).length]
    ];
    $("genealogy-stats").innerHTML=stats.map(([label,value])=>
      '<div class="genealogy-stat"><strong>'+escapeHtml(value)+'</strong><span>'+escapeHtml(label)+'</span></div>'
    ).join("");
  };
  const renderObjects = (data) => {
    $("genealogy-object-list").innerHTML=(data.research_objects||[]).map(item=>{
      const components=(item.components||[]).length
        ? '<h4>Components</h4><ul>'+(item.components||[]).map(x=>'<li>'+escapeHtml(x)+'</li>').join('')+'</ul>'
        : '';
      const evidence=(item.date_evidence||[]).length
        ? '<h4>Date and archival evidence</h4><ul class="genealogy-archive-list">'+(item.date_evidence||[]).map(x=>'<li>'+escapeHtml(x.title)+' · '+link(x.url,"Open source record")+' <span class="genealogy-muted">('+escapeHtml(x.role)+')</span></li>').join('')+'</ul>'
        : '';
      const publications=(item.publication_records||[]).length
        ? '<h4>Publication and institutional records</h4><ul>'+(item.publication_records||[]).map(x=>'<li>'+escapeHtml(x.title)+' · '+link(x.url,x.record_type||"Open record")+'</li>').join('')+'</ul>'
        : '';
      const detail=(components||evidence||publications)
        ? '<details class="genealogy-details"><summary>Components and source evidence</summary>'+components+evidence+publications+'</details>'
        : '';
      return '<article class="genealogy-card" id="object-'+escapeHtml(item.id)+'"><h3>'+escapeHtml(item.title)+'</h3><div class="genealogy-meta"><span class="genealogy-pill">'+escapeHtml(item.object_type)+'</span></div>'+
        '<p>'+escapeHtml(item.description)+'</p><p class="genealogy-muted">'+escapeHtml(item.role_in_genealogy)+'</p>'+
        '<div class="genealogy-links">'+link(item.uri,"Open source object")+'</div>'+detail+'</article>';
    }).join("");
    show("genealogy-objects");
  };
  const renderProcesses = (data) => {
    $("genealogy-process-list").innerHTML=(data.research_processes||[]).map(item=>
      '<article class="genealogy-card" id="process-'+escapeHtml(item.id)+'"><h3>'+escapeHtml(item.title)+'</h3><div class="genealogy-meta"><span class="genealogy-pill">'+escapeHtml(item.status)+'</span></div>'+
      '<p>'+escapeHtml(item.summary)+'</p><h4>Characteristics</h4><ul>'+
      (item.process_characteristics||[]).map(x=>'<li>'+escapeHtml(x)+'</li>').join('')+'</ul></article>'
    ).join("");
    show("genealogy-processes");
  };
  const renderClusters = (data) => {
    $("genealogy-cluster-list").innerHTML=(data.research_clusters||[]).map(cluster=>
      '<article class="genealogy-card"><h3>'+escapeHtml(cluster.title)+'</h3>'+
      '<div class="genealogy-meta"><span class="genealogy-pill">'+escapeHtml(cluster.cluster_type)+'</span><span class="genealogy-pill">'+(cluster.members||[]).length+' members</span></div>'+
      '<p>'+escapeHtml(cluster.description)+'</p><details class="genealogy-details"><summary>Membership and basis</summary><p>'+escapeHtml(cluster.membership_basis)+'</p><ul>'+
      (cluster.members||[]).map(m=>'<li><a href="#artifact-'+encodeURIComponent(m.artefact_id)+'">'+escapeHtml(m.artefact_id)+'</a> <span class="genealogy-muted">— '+escapeHtml(m.relationship)+'</span></li>').join("")+
      '</ul></details></article>'
    ).join("");
    show("genealogy-clusters");
  };
  const renderThreads = (data) => {
    $("genealogy-thread-list").innerHTML=(data.intellectual_threads||[]).map(thread=>
      '<article class="genealogy-card" id="thread-'+escapeHtml(thread.id)+'"><h3>'+escapeHtml(thread.title)+'</h3>'+
      '<p>'+escapeHtml(thread.description)+'</p><h4>Expressions in the research objects</h4><ul>'+
      (thread.expressions||[]).map(item=>'<li>'+escapeHtml(item.expression)+' <span class="genealogy-muted">Source object: <a href="#object-'+encodeURIComponent(item.research_object_id)+'">'+escapeHtml(item.research_object_id)+'</a></span></li>').join('')+
      '</ul></article>'
    ).join("");
    show("genealogy-threads");
  };
  const renderTimeline = (data) => {
    const items=captureEvents(data);
    $("genealogy-timeline-list").innerHTML=items.map(item=>
      '<article class="genealogy-event"><time datetime="'+escapeHtml(item.date)+'">'+escapeHtml(dateText(item.date))+'</time>'+
      '<div><div class="genealogy-meta"><span class="genealogy-pill">'+escapeHtml(item.kind)+'</span></div>'+
      '<h3>'+escapeHtml(item.title)+'</h3><p>'+escapeHtml(item.description)+'</p>'+
      (item.url?'<p>'+link(item.url,"Source")+'</p>':'')+
      '<p class="genealogy-muted">Date basis: '+escapeHtml(item.dateBasis||"not specified")+'</p></div></article>'
    ).join("")||'<p class="genealogy-muted">No timestamped events are currently available.</p>';
    show("genealogy-timeline");
  };
  const captureList = (captures) => {
    if (!captures||!captures.length) return '<p class="genealogy-muted">No archive capture locator supplied.</p>';
    return '<ul class="genealogy-archive-list">'+captures.map(c=>
      '<li><strong>'+escapeHtml(c.archive_service)+'</strong> · '+
      (c.captured_at?escapeHtml(dateText(c.captured_at)):"timestamp unknown")+' · '+link(c.url,"Archive locator")+
      '<br><span>'+escapeHtml(c.capture_status||"status not recorded")+' — '+escapeHtml(c.note||"")+'</span></li>'
    ).join("")+'</ul>';
  };
  let registry;
  const renderArtifacts = () => {
    const query=$("genealogy-search").value.trim().toLowerCase();
    const platform=$("genealogy-platform").value;
    const type=$("genealogy-type").value;
    const all=registry.artefacts||[];
    const filtered=all.filter(item=>{
      const haystack=[item.title,item.url,item.platform,item.artefact_type,item.summary,item.research_role].join(" ").toLowerCase();
      return (!query||haystack.includes(query))&&(!platform||item.platform===platform)&&(!type||item.artefact_type===type);
    });
    $("genealogy-results-count").textContent=filtered.length+" of "+all.length+" artefact records";
    $("genealogy-artifact-list").innerHTML=filtered.map(item=>{
      const captures=archiveCaptures(item),reps=item.representations||[];
      return '<article class="genealogy-card" id="artifact-'+escapeHtml(item.id)+'"><h3>'+escapeHtml(item.title)+'</h3>'+
        '<div class="genealogy-meta"><span class="genealogy-pill">'+escapeHtml(item.platform)+'</span><span class="genealogy-pill">'+escapeHtml(item.artefact_type)+'</span><span class="genealogy-pill">'+escapeHtml(item.review_status)+'</span></div>'+
        '<p>'+escapeHtml(item.summary)+'</p><p class="genealogy-muted">'+escapeHtml(item.research_role)+'</p>'+
        '<div class="genealogy-links">'+link(item.url,"Original platform record")+'</div>'+
        (reps.length?'<details class="genealogy-details"><summary>Additional manifestations ('+reps.length+')</summary>'+reps.map(rep=>
          '<p><strong>'+escapeHtml(rep.platform)+'</strong> · '+escapeHtml(rep.representation_type)+'<br>'+link(rep.url,rep.title||"Open representation")+
          '<br><span class="genealogy-muted">'+escapeHtml(rep.relation)+' · '+escapeHtml(rep.relationship_status)+'<br>'+escapeHtml(rep.evidence_basis)+'</span>'+
          captureList(rep.archive_captures)+'</p>'
        ).join("")+'</details>':'')+
        '<details class="genealogy-details"><summary>Archive observations ('+captures.length+')</summary>'+captureList(item.archive_captures||[])+'</details>'+
        '<details class="genealogy-details"><summary>Provenance and curation</summary><p>'+escapeHtml(item.provenance?.basis||"")+'</p><p class="genealogy-muted">Review: '+escapeHtml(item.review_status||"")+'</p>'+
        (item.curation_note?'<p>'+escapeHtml(item.curation_note)+'</p>':'')+'</details></article>';
    }).join("")||'<p class="genealogy-muted">No matching records. Adjust the search or filters.</p>';
  };
  const initFilters = (data) => {
    const platforms=[...new Set((data.artefacts||[]).map(x=>x.platform).filter(Boolean))].sort();
    const types=[...new Set((data.artefacts||[]).map(x=>x.artefact_type).filter(Boolean))].sort();
    $("genealogy-platform").innerHTML+platforms.map(x=>'<option value="'+escapeHtml(x)+'">'+escapeHtml(x)+'</option>').join("");
    $("genealogy-type").innerHTML+types.map(x=>'<option value="'+escapeHtml(x)+'">'+escapeHtml(x)+'</option>').join("");
    $("genealogy-search").addEventListener("input",renderArtifacts);
    $("genealogy-platform").addEventListener("change",renderArtifacts);
    $("genealogy-type").addEventListener("change",renderArtifacts);
  };
  const renderCollections = (data) => {
    $("genealogy-collection-list").innerHTML=(data.source_collections||[]).map(item=>
      '<article class="genealogy-card"><h3>'+escapeHtml(item.title)+'</h3><div class="genealogy-meta"><span class="genealogy-pill">'+escapeHtml(item.platform)+'</span></div>'+
      '<p>'+escapeHtml(item.content_scope||"")+'</p><div class="genealogy-links">'+link(item.url,"Primary index")+
      (item.representations||[]).map(r=>link(r.url,r.platform+" index")).join("")+'</div></article>'
    ).join("");
    show("genealogy-collections");
  };
  const renderLeads = (data) => {
    $("genealogy-lead-list").innerHTML=(data.inventory_leads||[]).map(item=>
      '<article class="genealogy-card"><h3>'+escapeHtml(item.title)+'</h3><div class="genealogy-meta"><span class="genealogy-pill">'+escapeHtml(item.discovery_status)+'</span></div>'+
      '<p>'+escapeHtml(item.summary)+'</p>'+(item.url?'<div class="genealogy-links">'+link(item.url,"Unmatched reference")+'</div>':'')+'</article>'
    ).join("");
    show("genealogy-leads");
  };
  const load = async () => {
    try {
      const response=await fetch(DATA_URL,{cache:"no-cache"});
      if(!response.ok) throw new Error("HTTP "+response.status);
      registry=await response.json();
      renderStats(registry);renderObjects(registry);renderProcesses(registry);renderClusters(registry);renderThreads(registry);
      renderTimeline(registry);initFilters(registry);renderArtifacts();renderCollections(registry);renderLeads(registry);
      $("genealogy-load-status").hidden=true;
    } catch(error) {
      $("genealogy-load-status").textContent="The Research Genealogy registry could not be loaded ("+error.message+"). The machine-readable registry remains available from the link above.";
    }
  };
  document.addEventListener("DOMContentLoaded",load);
})();