HTML = """
<!doctype html>
<html>
<head>
<title>Label Verifier</title>
<style>
body{font-family:Arial;margin:32px;max-width:1200px}
input,textarea,button,select{width:100%;margin:8px 0;padding:10px;box-sizing:border-box}
table{border-collapse:collapse;width:100%;margin-top:16px}
td,th{border:1px solid #ccc;padding:8px;text-align:left}
.match{background:#e7f7e7}.mismatch{background:#ffe8e8}.review{background:#fff6d5}
.filebox{border:1px solid #ccc;padding:12px;margin-top:18px}
pre{white-space:pre-wrap;max-height:420px;overflow:auto}
.formgrid{display:grid;grid-template-columns:220px 1fr;gap:8px 14px;align-items:center}
.section{border:1px solid #ddd;padding:16px;margin:18px 0;background:#fafafa}
.checkrow{display:grid;grid-template-columns:30px 1fr;gap:8px;align-items:center;margin:6px 0}
.checkrow input{width:auto;margin:0}
.small{font-size:13px;color:#555}
.warning{background:#fff6d5;border:1px solid #e5d27a;padding:10px;margin:10px 0}
</style>
</head>
<body>

<h1>Alcohol Label Verification Prototype</h1>
<p>Upload front/back labels, TTB application PDFs, multiple forms, or a ZIP containing images/PDFs.</p>

<div class="section">
<h2>Application Builder</h2>

<div class="formgrid">
<label>Product Category</label>
<select id="product_category" onchange="applyCategoryDefaults(); buildApplication();">
<option value="wine">Wine</option>
<option value="beer" selected>Beer / Malt Beverage</option>
<option value="spirits">Distilled Spirits</option>
</select>

<label>Brand Name</label><input type="text" id="brand_name" value="Bud Light">
<label>Class / Type</label><input type="text" id="class_type" value="Lager Beer">
<label>Alcohol Content (% ABV)</label><input type="number" id="alcohol_content" step="0.01" value="4.2">
<label>Net Contents</label><input type="text" id="net_contents" value="12 oz">
<label>Producer / Bottler</label><input type="text" id="producer_name" value="Anheuser-Busch">
<label>Country of Origin</label><input type="text" id="country_of_origin" value="United States">
<label>Appellation / Region</label><input type="text" id="appellation" value="">
<label>Vintage</label><input type="text" id="vintage" value="">
</div>

<h3>Required Compliance Elements</h3>
<div class="checkrow"><input type="checkbox" id="government_warning" checked><label>Government Warning Required</label></div>
<div class="checkrow"><input type="checkbox" id="abv_required"><label>ABV Required / Declared</label></div>
<div class="checkrow"><input type="checkbox" id="sulfites_required"><label>Sulfites Declaration Required</label></div>
<div class="checkrow"><input type="checkbox" id="producer_required" checked><label>Producer / Bottler Information Required</label></div>
<div class="checkrow"><input type="checkbox" id="origin_required"><label>Country of Origin Required</label></div>
<div class="checkrow"><input type="checkbox" id="organic_required"><label>Organic Claims Present / Require Review</label></div>
<div class="checkrow"><input type="checkbox" id="formula_review_required"><label>Formula Approval Review Required</label></div>

<details><summary>Show generated application JSON</summary><pre id="jsonpreview"></pre></details>
</div>

<div class="section">
<h2>Single Label Set / Single PDF Form</h2>

<div class="warning">
<strong>Best practice:</strong> Upload the application PDF plus front and back labels when available.
</div>

<label>TTB Application Form PDF</label>
<input type="file" id="application_form" accept=".pdf">

<label>Front Label Image</label>
<input type="file" id="front_image" accept="image/*">

<label>Back Label Image</label>
<input type="file" id="back_image" accept="image/*">

<label>Other / Neck / Additional Label Images or PDFs</label>
<input type="file" id="other_images" accept="image/*,.pdf" multiple>

<label>Optional pasted label text</label>
<textarea id="labeltext" rows="8"></textarea>

<button onclick="runSingle()">Validate Label Set</button>
</div>

<div class="section">
<h2>Batch Upload</h2>

<label>Batch Label Images</label>
<input type="file" id="batch_images" accept="image/*" multiple>

<label>Batch TTB Forms / PDFs</label>
<input type="file" id="batch_forms" accept=".pdf" multiple>

<label>Or ZIP of Images/PDFs</label>
<input type="file" id="zip_file" accept=".zip">

<button onclick="runBatch()">Batch Validate</button>
</div>

<div id="out"></div>

<script>
function applyCategoryDefaults(){
 const category = document.getElementById('product_category').value;
 document.getElementById('government_warning').checked = true;
 document.getElementById('producer_required').checked = true;

 if(category === 'spirits'){
   document.getElementById('abv_required').checked = true;
   document.getElementById('sulfites_required').checked = false;
   document.getElementById('organic_required').checked = false;
 }

 if(category === 'wine'){
   document.getElementById('abv_required').checked = true;
   document.getElementById('sulfites_required').checked = true;
 }

 if(category === 'beer'){
   document.getElementById('abv_required').checked = false;
   document.getElementById('sulfites_required').checked = false;
   document.getElementById('organic_required').checked = false;
 }
}

function buildApplication(){
 const alcoholRaw = document.getElementById('alcohol_content').value;
 const app = {
   product_category: document.getElementById('product_category').value,
   brand_name: document.getElementById('brand_name').value.trim(),
   class_type: document.getElementById('class_type').value.trim(),
   alcohol_content: alcoholRaw === '' ? null : parseFloat(alcoholRaw),
   net_contents: document.getElementById('net_contents').value.trim(),
   producer_name: document.getElementById('producer_name').value.trim(),
   country_of_origin: document.getElementById('country_of_origin').value.trim(),
   appellation: document.getElementById('appellation').value.trim(),
   vintage: document.getElementById('vintage').value.trim(),
   government_warning_required: document.getElementById('government_warning').checked,
   abv_required: document.getElementById('abv_required').checked,
   sulfites_required: document.getElementById('sulfites_required').checked,
   producer_required: document.getElementById('producer_required').checked,
   origin_required: document.getElementById('origin_required').checked,
   organic_required: document.getElementById('organic_required').checked,
   formula_review_required: document.getElementById('formula_review_required').checked
 };
 document.getElementById('jsonpreview').textContent = JSON.stringify(app,null,2);
 return app;
}

function renderSummary(data){
 const meta = data.metadata || {};
 const q = meta.ocr_quality || {};
 return `<div class="section">
   <strong>Summary:</strong>
   Matches: ${data.summary?.matches ?? 0} |
   Mismatches: ${data.summary?.mismatches ?? 0} |
   Reviews: ${data.summary?.reviews ?? 0}
   <br><span class="small">OCR Quality: ${q.quality ?? 'unknown'} | Words: ${q.word_count ?? 0} | Warning Score: ${q.warning_score ?? 0}</span>
   <br><span class="small">Views: ${(meta.image_views || []).join(', ') || 'none'} | Front/back: ${meta.front_and_back_supplied ? 'yes' : 'no'}</span>
 </div>`;
}

function renderResult(title, data){
 let html=`<div class="filebox"><h2>${title}</h2>`;
 html += renderSummary(data);

 if(data.form_fields && Object.keys(data.form_fields).length){
   html += '<details><summary>Extracted PDF Form Fields</summary><pre>' + JSON.stringify(data.form_fields,null,2) + '</pre></details>';
 }

 if(data.document_items){
   const bad = data.document_items.filter(x => x && x.error);
   if(bad.length){
     html += '<h3>Document/OCR Warnings</h3><pre>' + JSON.stringify(bad,null,2) + '</pre>';
   }
 }

 if(data.ocr_text){
   html += `<details><summary>OCR / Extracted Text</summary><pre>${data.ocr_text}</pre></details>`;
 }

 html+='<table><tr><th>Field</th><th>Application</th><th>Label</th><th>Status</th><th>Confidence</th><th>Rule</th></tr>';
 for(const r of data.results || []){
   html+=`<tr class="${r.status}"><td>${r.field}</td><td>${r.application??''}</td><td>${r.label??''}</td><td>${r.status}</td><td>${r.confidence}</td><td>${r.rule}</td></tr>`;
 }
 html+='</table></div>';
 return html;
}

async function postForm(url, fd){
 const res = await fetch(url,{method:'POST',body:fd});
 const raw = await res.text();
 try { return JSON.parse(raw); }
 catch(e){ return {error:'Server returned non-JSON response', raw}; }
}

async function runSingle(){
 const fd=new FormData();
 const app=buildApplication();

 fd.append('application_json', JSON.stringify(app));
 fd.append('label_text', document.getElementById('labeltext').value);

 const form=document.getElementById('application_form').files[0];
 const front=document.getElementById('front_image').files[0];
 const back=document.getElementById('back_image').files[0];
 const others=document.getElementById('other_images').files;

 if(form){ fd.append('application_form', form); }
 if(front){ fd.append('front_image', front); }
 if(back){ fd.append('back_image', back); }
 for(const file of others){ fd.append('other_images', file); }

 document.getElementById('out').innerHTML='<h2>Results</h2><p>Processing document OCR...</p>';

 const data=await postForm('/validate', fd);

 if(data.error){
   document.getElementById('out').innerHTML='<h2>Error</h2><pre>'+JSON.stringify(data,null,2)+'</pre>';
   return;
 }

 document.getElementById('out').innerHTML='<h2>Results</h2>' + renderResult('Label/Form Set', data);
}

async function runBatch(){
 const fd=new FormData();
 const app=buildApplication();

 fd.append('application_json', JSON.stringify(app));

 const batchImages=document.getElementById('batch_images').files;
 const batchForms=document.getElementById('batch_forms').files;
 const zip=document.getElementById('zip_file').files[0];

 for(const file of batchImages){ fd.append('images', file); }
 for(const file of batchForms){ fd.append('forms', file); }
 if(zip){ fd.append('zip_file', zip); }

 document.getElementById('out').innerHTML='<h2>Batch Results</h2><p>Processing batch documents...</p>';

 const data=await postForm('/batch-validate', fd);

 if(data.error){
   document.getElementById('out').innerHTML='<h2>Error</h2><pre>'+JSON.stringify(data,null,2)+'</pre>';
   return;
 }

 let html='<h2>Batch Results</h2>';
 for(const item of data.batch_results || []){
   html += renderResult(item.filename || 'Batch Item', item);
 }

 document.getElementById('out').innerHTML=html;
}

document.querySelectorAll('input,textarea,select').forEach(el => el.addEventListener('input', buildApplication));
document.addEventListener('DOMContentLoaded', function(){ applyCategoryDefaults(); buildApplication(); });
</script>
</body>
</html>
"""
