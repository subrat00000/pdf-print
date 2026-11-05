// PDF Scale & Print — Manifest V3 service worker
// Detects online PDFs from response headers/URLs and local PDFs from file:// navigation.
// For local files, the user must enable "Allow access to file URLs" in extension details.

const EDITOR_URL = chrome.runtime.getURL("editor.html");
const recentlyOpened = new Map();

function isEditorUrl(url) {
  return typeof url === "string" && url.startsWith(EDITOR_URL);
}

function looksLikePdfUrl(rawUrl) {
  try {
    const u = new URL(rawUrl);
    if (!["http:", "https:", "file:"].includes(u.protocol)) return false;
    return /\.pdf$/i.test(decodeURIComponent(u.pathname));
  } catch {
    return false;
  }
}

function responseLooksLikePdf(headers) {
  for (const h of (headers || [])) {
    const name = String(h.name || "").toLowerCase();
    const value = String(h.value || "").toLowerCase();
    if (name === "content-type") {
      const mime = value.split(";")[0].trim();
      if (["application/pdf", "application/x-pdf", "application/acrobat", "applications/vnd.pdf"].includes(mime)) return true;
    }
    if (name === "content-disposition" && /\.pdf(?:["';]|$)/i.test(value)) return true;
  }
  return false;
}

function openEditor(tabId, pdfUrl, reason) {
  if (!Number.isInteger(tabId) || tabId < 0 || !pdfUrl || isEditorUrl(pdfUrl)) return;
  let protocol;
  try { protocol = new URL(pdfUrl).protocol; } catch { return; }
  if (!["http:", "https:", "file:"].includes(protocol)) return;
  if (!looksLikePdfUrl(pdfUrl) && protocol === "file:") return;

  const now = Date.now();
  const previous = recentlyOpened.get(tabId);
  if (previous && previous.url === pdfUrl && now - previous.time < 15000) return;
  recentlyOpened.set(tabId, { url: pdfUrl, time: now });

  const editor = `${EDITOR_URL}?url=${encodeURIComponent(pdfUrl)}&detected=${encodeURIComponent(reason)}`;
  chrome.tabs.update(tabId, { url: editor }, () => {
    if (chrome.runtime.lastError) {
      console.warn("PDF Scale & Print:", chrome.runtime.lastError.message);
      recentlyOpened.delete(tabId);
    }
  });
}

// Online PDF endpoints, including URLs without a .pdf suffix.
chrome.webRequest.onHeadersReceived.addListener(
  details => {
    if (details.tabId < 0 || details.type !== "main_frame") return;
    if (responseLooksLikePdf(details.responseHeaders)) openEditor(details.tabId, details.url, "response-header");
  },
  { urls: ["http://*/*", "https://*/*"], types: ["main_frame"] },
  ["responseHeaders"]
);

// Navigation detection handles .pdf URLs, including file:///C:/.../document.pdf.
// The file URL listener only works after "Allow access to file URLs" is enabled.
chrome.webNavigation.onCommitted.addListener(details => {
  if (details.frameId !== 0 || details.tabId < 0 || isEditorUrl(details.url)) return;
  if (looksLikePdfUrl(details.url)) openEditor(details.tabId, details.url, "navigation-url");
});

// Fallback for browsers that report the final URL through tabs.onUpdated.
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (isEditorUrl(tab.url)) return;
  const candidate = changeInfo.url || tab.url;
  if (candidate && looksLikePdfUrl(candidate)) openEditor(tabId, candidate, "tab-url-update");
});

// Clicking the toolbar button opens the current PDF, or the editor for manual selection.
chrome.action.onClicked.addListener(tab => {
  if (!tab || !Number.isInteger(tab.id) || !tab.url || isEditorUrl(tab.url)) {
    chrome.tabs.create({ url: EDITOR_URL });
    return;
  }
  if (looksLikePdfUrl(tab.url)) {
    openEditor(tab.id, tab.url, "toolbar-click");
  } else {
    chrome.tabs.create({ url: EDITOR_URL });
  }
});

chrome.tabs.onRemoved.addListener(tabId => recentlyOpened.delete(tabId));
