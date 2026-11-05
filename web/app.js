(() => {
"use strict";
pdfjsLib.GlobalWorkerOptions.workerSrc = chrome.runtime.getURL("vendor/pdf.worker.min.js");
const $ = id => document.getElementById(id);
const state = {pdf:null,bytes:null,name:"document.pdf",pageCount:0,activePage:1,zoom:1,observer:null,rendered:new Set(),rendering:new Set(),pageSizes:[]};
const PAPER = {A4:[595.276,841.89],A3:[841.89,1190.55],Letter:[612,792],Legal:[612,1008]};
const showToast = msg => {const t=$("toast");t.textContent=msg;t.style.display="block";clearTimeout(showToast.timer);showToast.timer=setTimeout(()=>t.style.display="none",2800)};
const status = msg => $("status").textContent=msg;
const num = id => Math.max(0,Number($(id).value)||0);
const getPaper = () => {let [w,h]=PAPER[$("paper").value];if($("orientation").value==="landscape")[w,h]=[h,w];return [w,h]};
const mmToPt = mm => mm*72/25.4;
const getLayout = () => ({paper:getPaper(),margins:{top:mmToPt(num("mTop")),bottom:mmToPt(num("mBottom")),left:mmToPt(num("mLeft")),right:mmToPt(num("mRight"))},h:$("hAlign").value,v:$("vAlign").value,mode:$("scaleMode").value,scale:Math.min(5,Math.max(.01,(Number($("scale").value)||85)/100))});
const SETTINGS_KEY = "pdfScalePrintLastLayout";
const SETTINGS_FIELDS = ["paper","orientation","scale","scaleMode","hAlign","vAlign","mTop","mBottom","mLeft","mRight","printScope","pageRange"];
let settingsReady = false;
let settingsTimer = null;
function collectSettings(){
 const data={};
 for(const id of SETTINGS_FIELDS)data[id]=$(id).value;
 return data;
}
async function saveSettings(){
 if(!settingsReady || !chrome.storage?.local)return;
 clearTimeout(settingsTimer);
 settingsTimer=setTimeout(()=>{
  chrome.storage.local.set({[SETTINGS_KEY]:collectSettings()},()=>{
   if(chrome.runtime.lastError)console.warn("Could not save PDF layout settings:",chrome.runtime.lastError.message);
  });
 },250);
}
async function restoreSettings(){
 if(!chrome.storage?.local){settingsReady=true;return;}
 try{
  const result=await chrome.storage.local.get(SETTINGS_KEY);
  const saved=result[SETTINGS_KEY]||{};
  for(const id of SETTINGS_FIELDS){
   if(saved[id]!==undefined && $(id))$(id).value=String(saved[id]);
  }
  $("scale").disabled=$("scaleMode").value!=="manual";
  $("pageRange").disabled=$("printScope").value!=="range";
 }catch(err){console.warn("Could not restore saved PDF layout:",err);}
 settingsReady=true;
}

function setEnabled(on){["pageJump","zoomIn","zoomOut","printBtn","downloadBtn"].forEach(id=>$(id).disabled=!on);$("pageJump").max=state.pageCount||1}
function validPdf(file){return !!file && (file.type==="application/pdf" || file.name.toLowerCase().endsWith(".pdf"))}
async function openFile(file){
 if(!validPdf(file)){showToast("Please select a PDF file only.");return}
 try{
  status("Loading PDF…");
  const bytes=await file.arrayBuffer();
  const task=pdfjsLib.getDocument({data:new Uint8Array(bytes.slice(0))});
  const pdf=await task.promise;
  if(state.observer)state.observer.disconnect();
  state.pdf=pdf;state.bytes=bytes;state.name=file.name;state.pageCount=pdf.numPages;state.activePage=1;state.rendered.clear();state.rendering.clear();state.pageSizes=[];
  $("pages").replaceChildren();$("pageCount").textContent="/ "+state.pageCount;$("pageJump").value=1;
  $("pageRange").disabled=$("printScope").value!=="range";
  state.observer=new IntersectionObserver(entries=>{
   let best=null;
   for(const e of entries){if(e.isIntersecting){const ratio=e.intersectionRatio;if(!best||ratio>best.ratio)best={ratio,page:Number(e.target.dataset.page)}}}
   if(best){state.activePage=best.page;$("pageJump").value=best.page}
   for(const e of entries)if(e.isIntersecting)renderPage(Number(e.target.dataset.page));
  },{root:$("pages"),threshold:[.1,.25,.5,.75]});
  for(let n=1;n<=state.pageCount;n++){
   const wrap=document.createElement("div");wrap.className="page-wrap";wrap.dataset.page=n;
  const [paperW,paperH]=getPaper();wrap.style.aspectRatio=`${paperW} / ${paperH}`;
   const label=document.createElement("span");label.className="page-label";label.textContent=`Page ${n}`;
   const canvas=document.createElement("canvas");canvas.setAttribute("aria-label",`PDF page ${n}`);
   wrap.append(label,canvas);$("pages").append(wrap);state.observer.observe(wrap);
  }
  setEnabled(true);const empty=$("empty");if(empty)empty.remove();status(`${file.name} · ${state.pageCount} pages`);
  await renderPage(1);
 }catch(err){console.error(err);status("Could not open PDF");showToast("Unable to open this PDF. It may be damaged or encrypted.");}
}
async function renderPage(n){
 if(!state.pdf||state.rendered.has(n)||state.rendering.has(n))return;
 state.rendering.add(n);
 try{
  const page=await state.pdf.getPage(n);const layout=getLayout();const [pw,ph]=layout.paper;
  const m=layout.margins;const aw=Math.max(1,pw-m.left-m.right),ah=Math.max(1,ph-m.top-m.bottom);
  const vp=page.getViewport({scale:1});
  let scale=layout.scale;
  if(layout.mode==="fit")scale=Math.min(aw/vp.width,ah/vp.height);
  if(layout.mode==="actual")scale=1;
  const cw=vp.width*scale,ch=vp.height*scale;
  const x=m.left+(layout.h==="left"?0:layout.h==="right"?aw-cw:(aw-cw)/2);
  const yTop=m.top+(layout.v==="top"?0:layout.v==="bottom"?ah-ch:(ah-ch)/2);
  const wrap=$("pages").querySelector(`.page-wrap[data-page="${n}"]`);
  const canvas=wrap.querySelector("canvas");
  const cssW=wrap.clientWidth || 760,cssH=cssW*ph/pw;
  const displayScale=cssW/pw;
  canvas.width=Math.round(cssW*devicePixelRatio);canvas.height=Math.round(cssH*devicePixelRatio);
  canvas.style.width=cssW+"px";canvas.style.height=cssH+"px";
  const ctx=canvas.getContext("2d");
  ctx.fillStyle="#fff";ctx.fillRect(0,0,canvas.width,canvas.height);
  const contentVp=page.getViewport({scale:displayScale*scale});
  const offsetX=x*displayScale,offsetY=yTop*displayScale;
  await page.render({canvasContext:ctx,viewport:contentVp,transform:[devicePixelRatio,0,0,devicePixelRatio,offsetX*devicePixelRatio,offsetY*devicePixelRatio]}).promise;
  state.rendered.add(n);
 }catch(e){console.error("Page render",n,e);const c=$("pages").querySelector(`.page-wrap[data-page="${n}"] canvas`);if(c){const ctx=c.getContext("2d");ctx.font="14px sans-serif";ctx.fillStyle="#a33";ctx.fillText("Preview could not be rendered",12,30)}}
 finally{state.rendering.delete(n)}
}
async function refreshPreviews(){
 if(!state.pdf)return;
 state.rendered.clear();
 const [paperW,paperH]=getPaper();document.querySelectorAll(".page-wrap").forEach(w=>w.style.aspectRatio=`${paperW} / ${paperH}`);
 const canvases=$("pages").querySelectorAll("canvas");canvases.forEach(c=>{c.width=1;c.height=1;c.style.width="1px";c.style.height="1px"});
 // render the current page and pages currently in/near the viewport
 const visible=[...$("pages").querySelectorAll(".page-wrap")].filter(el=>{const r=el.getBoundingClientRect(),v=$("pages").getBoundingClientRect();return r.bottom>=v.top-500&&r.top<=v.bottom+500}).map(el=>Number(el.dataset.page));
 for(const n of visible)await renderPage(n);
}
let refreshTimer;
["paper","orientation","scale","scaleMode","hAlign","vAlign","mTop","mBottom","mLeft","mRight"].forEach(id=>{
 $(id).addEventListener("change",()=>{if(id==="scaleMode")$("scale").disabled=$("scaleMode").value!=="manual";saveSettings();clearTimeout(refreshTimer);refreshTimer=setTimeout(refreshPreviews,160)});
});
$("scaleMode").addEventListener("change",()=>{$("scale").disabled=$("scaleMode").value!=="manual"});
$("dropzone").addEventListener("click",()=>$("fileInput").click());
$("dropzone").addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" ")$("fileInput").click()});
$("openBtn").addEventListener("click",()=>$("fileInput").click());
$("fileInput").addEventListener("change",e=>{if(e.target.files[0])openFile(e.target.files[0]);e.target.value=""});
["dragenter","dragover"].forEach(type=>$("dropzone").addEventListener(type,e=>{e.preventDefault();$("dropzone").classList.add("drag")}));
["dragleave","drop"].forEach(type=>$("dropzone").addEventListener(type,e=>{e.preventDefault();$("dropzone").classList.remove("drag")}));
$("dropzone").addEventListener("drop",e=>{const files=[...e.dataTransfer.files];if(files.length!==1||!validPdf(files[0])){showToast("Drop exactly one PDF file.");return}openFile(files[0])});
$("pages").addEventListener("dragover",e=>e.preventDefault());
$("pages").addEventListener("drop",e=>{e.preventDefault();const f=[...e.dataTransfer.files];if(f.length===1&&validPdf(f[0]))openFile(f[0]);else showToast("Drop exactly one PDF file.")});
$("pages").addEventListener("scroll",()=>{const mid=$("pages").getBoundingClientRect().top+$("pages").clientHeight/2;let closest=null,dist=Infinity;document.querySelectorAll(".page-wrap").forEach(el=>{const r=el.getBoundingClientRect(),d=Math.abs((r.top+r.bottom)/2-mid);if(d<dist){dist=d;closest=Number(el.dataset.page)}});if(closest){state.activePage=closest;$("pageJump").value=closest}});
$("pageJump").addEventListener("change",()=>{const n=Math.min(state.pageCount,Math.max(1,Number($("pageJump").value)||1));$("pages").querySelector(`.page-wrap[data-page="${n}"]`)?.scrollIntoView({behavior:"smooth",block:"start"});state.activePage=n});
$("zoomIn").addEventListener("click",()=>{state.zoom=Math.min(2,state.zoom+.1);$("zoomText").textContent=Math.round(state.zoom*100)+"%";$("pages").style.zoom=state.zoom});
$("zoomOut").addEventListener("click",()=>{state.zoom=Math.max(.5,state.zoom-.1);$("zoomText").textContent=Math.round(state.zoom*100)+"%";$("pages").style.zoom=state.zoom});
$("printScope").addEventListener("change",()=>{$("pageRange").disabled=$("printScope").value!=="range";saveSettings()});
$("pageRange").addEventListener("change",saveSettings);
function parseRange(value,max){
 const out=[],seen=new Set();if(!value.trim())throw Error("Enter page numbers, for example 1-3, 5.");
 for(const p of value.split(",")){const s=p.trim();if(!s)throw Error("Invalid page range.");let a,b;if(s.includes("-")){const bits=s.split("-");if(bits.length!==2)throw Error("Invalid range.");a=Number(bits[0]);b=Number(bits[1])}else a=b=Number(s);if(!Number.isInteger(a)||!Number.isInteger(b)||a<1||b<a||b>max)throw Error(`Use page numbers from 1 to ${max}.`);for(let i=a;i<=b;i++)if(!seen.has(i)){seen.add(i);out.push(i-1)}}
 return out;
}
async function createOutput(indices){
 const layout=getLayout();
 const [pw,ph]=layout.paper,m=layout.margins;
 if(m.left+m.right>=pw||m.top+m.bottom>=ph)throw Error("Margins leave no printable area.");
 // Always give pdf-lib its own byte array; PDF.js may transfer its input buffer to the worker.
 const sourceBytes=new Uint8Array(state.bytes.slice(0));
 const out=await PDFLib.PDFDocument.create();
 const embedded=await out.embedPdf(sourceBytes,indices);
 const aw=pw-m.left-m.right,ah=ph-m.top-m.bottom;
 for(let j=0;j<embedded.length;j++){
  const emb=embedded[j],sw=emb.width,sh=emb.height;
  let scale=layout.scale;
  if(layout.mode==="fit")scale=Math.min(aw/sw,ah/sh);
  if(layout.mode==="actual")scale=1;
  const w=sw*scale,h=sh*scale;
  const x=m.left+(layout.h==="left"?0:layout.h==="right"?aw-w:(aw-w)/2);
  const yTop=m.top+(layout.v==="top"?0:layout.v==="bottom"?ah-h:(ah-h)/2);
  const page=out.addPage([pw,ph]);
  page.drawPage(emb,{x,y:ph-yTop-h,width:w,height:h});
 }
 return await out.save();
}
function getIndices(){
 const scope=$("printScope").value;
 if(scope==="current")return [state.activePage-1];
 if(scope==="all")return Array.from({length:state.pageCount},(_,i)=>i);
 return parseRange($("pageRange").value,state.pageCount);
}
$("downloadBtn").addEventListener("click",async()=>{
 try{const indices=Array.from({length:state.pageCount},(_,i)=>i);status("Preparing adjusted PDF…");const bytes=await createOutput(indices);const blob=new Blob([bytes],{type:"application/pdf"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=state.name.replace(/\.pdf$/i,"")+"_adjusted.pdf";a.click();setTimeout(()=>URL.revokeObjectURL(url),60000);status("Adjusted PDF downloaded");showToast("Adjusted PDF is ready.");}
 catch(e){console.error(e);showToast(e.message||"Could not create PDF.");status("PDF generation failed")}
});
$("printBtn").addEventListener("click",async()=>{
 let win=null;
 try{
  const indices=getIndices();status("Preparing print preview…");
  const bytes=await createOutput(indices);const blob=new Blob([bytes],{type:"application/pdf"});const url=URL.createObjectURL(blob);
  win=window.open(url,"_blank");
  if(!win){URL.revokeObjectURL(url);throw Error("The browser blocked the preview popup. Allow pop-ups for this local app and try again.")}
  status(`Print preview opened · ${indices.length} page(s)`);
  // The PDF viewer's print command invokes the browser/OS print preview.
  setTimeout(()=>URL.revokeObjectURL(url),120000);
 }catch(e){console.error(e);if(win)win.close();showToast(e.message||"Could not prepare print preview.");status("Print preview failed")}
});

async function openRemotePdf(url){
 try{
  const parsed=new URL(url);
  const isLocal=parsed.protocol==="file:";
  status(isLocal?"Loading local PDF…":"Fetching PDF from browser tab…");
  // file:// access is available only when the user enables the extension's
  // "Allow access to file URLs" permission in the browser's extension details.
  const response=await fetch(url,{credentials:isLocal?"omit":"include",redirect:"follow"});
  // file:// fetch responses may use status 0, so only enforce HTTP status checks.
  if(!isLocal&&!response.ok)throw Error(`Could not fetch PDF (${response.status}).`);
  const type=(response.headers.get("content-type")||"").toLowerCase();
  if(type&&!type.includes("application/pdf")&&!decodeURIComponent(parsed.pathname).toLowerCase().endsWith(".pdf"))
    throw Error("The selected file or page did not return a PDF file.");
  const blob=await response.blob();
  if(!blob.size)throw Error("The PDF file is empty or the browser did not grant access to it.");
  const rawName=decodeURIComponent(parsed.pathname.split("/").pop()||"document.pdf");
  const safeName=rawName.toLowerCase().endsWith(".pdf")?rawName:"document.pdf";
  const file=new File([blob],safeName,{type:"application/pdf"});
  await openFile(file);
 }catch(err){
  console.error(err);
  if(url.startsWith("file:")){
   status("Local PDF access was blocked");
   showToast("The browser blocked local-file access. Enable Allow access to file URLs, reload the extension, then reopen the PDF. You can also click Open PDF and select it manually.");
  }else{
   status("Could not load the browser PDF");
   showToast(err.message || "Unable to load this PDF. Try downloading it and opening it here.");
  }
 }
}

// Restore the previous paper, scale, alignment and four margins before loading
// the incoming PDF, so the first preview uses the last-used print layout.
(async()=>{
 await restoreSettings();
 const sourceUrl=new URLSearchParams(location.search).get("url");
 if(sourceUrl)openRemotePdf(sourceUrl);
})(); 
})();
