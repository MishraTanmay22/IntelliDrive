// IntelliDrive Advanced Client Controller

let currentCategory = 'all'; // 'all' | 'recent' | 'shared' | 'starred' | 'trash'
let currentFolderId = null;
let currentView = 'grid'; // 'grid' | 'list'
let searchQuery = '';
let currentTypeFilter = 'all';
let currentSort = 'newest';
let filesData = [];
let breadcrumbsData = [];
let selectedFileIds = new Set();
let activeContextMenu = null;

// DOM Elements
const fileGrid = document.getElementById('file-grid');
const fileList = document.getElementById('file-list');
const itemsCount = document.getElementById('items-count');
const breadcrumbContainer = document.getElementById('breadcrumb-container');
const searchInput = document.getElementById('search-input');
const searchClearBtn = document.getElementById('search-clear');
const fileInput = document.getElementById('file-input');
const uploadBtn = document.getElementById('upload-btn');
const newFolderBtn = document.getElementById('new-folder-btn');
const profileBtn = document.getElementById('profile-btn');
const profileDropdown = document.getElementById('profile-dropdown');
const dropzoneOverlay = document.getElementById('dropzone-overlay');
const uploadToastContainer = document.getElementById('upload-toast-container');
const storageProgressFill = document.getElementById('storage-progress-fill');
const storageTextUsed = document.getElementById('storage-text-used');
const storageTextDetail = document.getElementById('storage-text-detail');
const emptyState = document.getElementById('empty-state');
const categoryBanner = document.getElementById('category-banner');
const bannerText = document.getElementById('banner-text');
const bannerActionBtn = document.getElementById('banner-action-btn');
const sortSelect = document.getElementById('sort-select');
const batchBar = document.getElementById('batch-bar');
const batchCountText = document.getElementById('batch-count-text');

// View Buttons
const gridViewBtn = document.getElementById('grid-view-btn');
const listViewBtn = document.getElementById('list-view-btn');

// Mobile Sidebar
const hamburgerBtn = document.getElementById('hamburger-btn');
const sidebar = document.getElementById('sidebar');
const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
const sidebarOverlay = document.getElementById('sidebar-overlay');

// Modals
const newFolderModal = document.getElementById('new-folder-modal');
const newFolderNameInput = document.getElementById('folder-name-input');
const createFolderConfirmBtn = document.getElementById('create-folder-confirm-btn');

const previewModal = document.getElementById('preview-modal');
const previewModalTitle = document.getElementById('preview-modal-title');
const previewModalBody = document.getElementById('preview-modal-body');

const shareModal = document.getElementById('share-modal');
const shareModalTitle = document.getElementById('share-modal-title');
const shareLinkInput = document.getElementById('share-link-input');

const settingsModal = document.getElementById('settings-modal');
const upgradeModal = document.getElementById('upgrade-modal');
const logoutModal = document.getElementById('logout-modal');

// Icon Generator
function getIconForType(type, size = 48) {
  const s = size;
  switch (type) {
    case 'folder':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="#FCD34D" stroke="#F59E0B" stroke-width="0.5"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>`;
    case 'pdf':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`;
    case 'image':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`;
    case 'document':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>`;
    case 'video':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>`;
    case 'audio':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="#EC4899" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>`;
    case 'archive':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg>`;
    case 'code':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`;
    default:
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>`;
  }
}

// Fetch Files
async function fetchFiles() {
  try {
    const parentParam = currentFolderId ? currentFolderId : '';
    const url = `/api/files?category=${encodeURIComponent(currentCategory)}&parent_id=${encodeURIComponent(parentParam)}&search=${encodeURIComponent(searchQuery)}&type=${encodeURIComponent(currentTypeFilter)}&sort=${encodeURIComponent(currentSort)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.success) {
      filesData = data.files;
      breadcrumbsData = data.breadcrumbs || [];
      renderBreadcrumbs();
      renderFiles();
      updateStorageUI(data.storage);
    }
  } catch (err) {
    console.error('Error fetching files:', err);
  }
}

// Render Interactive Breadcrumbs
function renderBreadcrumbs() {
  if (!breadcrumbContainer) return;
  
  let html = `<span class="breadcrumb-item ${!currentFolderId ? 'active' : ''}" onclick="navigateToFolder(null, 'My Files')">My Files</span>`;

  if (currentCategory !== 'all') {
    const catLabels = { recent: 'Recent', starred: 'Starred', shared: 'Shared', trash: 'Trash' };
    html = `<span class="breadcrumb-item active">${catLabels[currentCategory] || currentCategory}</span>`;
    breadcrumbContainer.innerHTML = html;
    return;
  }

  breadcrumbsData.forEach((crumb, idx) => {
    const isLast = idx === breadcrumbsData.length - 1;
    html += `
      <span class="breadcrumb-separator">/</span>
      <span class="breadcrumb-item ${isLast ? 'active' : ''}" onclick="navigateToFolder('${crumb.id}', '${escapeHtml(crumb.name)}')">${escapeHtml(crumb.name)}</span>
    `;
  });

  breadcrumbContainer.innerHTML = html;
}

function navigateToFolder(folderId, folderName) {
  currentFolderId = folderId;
  clearSelection();
  fetchFiles();
}

// Update Storage UI
function updateStorageUI(storage) {
  if (!storage) return;
  if (storageProgressFill) {
    storageProgressFill.style.width = `${Math.min(storage.percentage, 100)}%`;
  }
  if (storageTextUsed) {
    storageTextUsed.textContent = `${storage.percentage}% Used`;
  }
  if (storageTextDetail) {
    storageTextDetail.textContent = `${storage.used_formatted} of ${storage.quota_formatted} used`;
  }
}

// Render Files
function renderFiles() {
  const count = filesData.length;
  itemsCount.textContent = `${count} ${count === 1 ? 'item' : 'items'}`;

  // Trash banner handling
  if (currentCategory === 'trash') {
    categoryBanner.classList.add('visible');
    bannerText.textContent = `Items in trash will be permanently deleted after 30 days.`;
    bannerActionBtn.textContent = 'Empty Trash';
    bannerActionBtn.style.display = count > 0 ? 'inline-block' : 'none';
    bannerActionBtn.onclick = emptyTrash;
  } else {
    categoryBanner.classList.remove('visible');
  }

  // Check empty state
  if (count === 0) {
    fileGrid.style.display = 'none';
    fileList.style.display = 'none';
    emptyState.classList.add('visible');
    const emptyTitle = document.getElementById('empty-title');
    const emptyDesc = document.getElementById('empty-desc');
    if (searchQuery) {
      emptyTitle.textContent = 'No matching files found';
      emptyDesc.textContent = `We couldn't find anything matching "${searchQuery}"`;
    } else if (currentCategory === 'trash') {
      emptyTitle.textContent = 'Trash is empty';
      emptyDesc.textContent = 'Items you delete will show up here.';
    } else if (currentCategory === 'starred') {
      emptyTitle.textContent = 'No starred files';
      emptyDesc.textContent = 'Star important files to quickly access them here.';
    } else if (currentCategory === 'shared') {
      emptyTitle.textContent = 'No shared files';
      emptyDesc.textContent = 'Files shared with you or shared by you will appear here.';
    } else if (currentFolderId) {
      emptyTitle.textContent = 'Folder is empty';
      emptyDesc.textContent = 'Upload files or create subfolders here.';
    } else {
      emptyTitle.textContent = 'No files uploaded yet';
      emptyDesc.textContent = 'Upload files or create folders to get started.';
    }
    return;
  }

  emptyState.classList.remove('visible');

  if (currentView === 'grid') {
    fileGrid.style.display = 'grid';
    fileList.style.display = 'none';
    renderGridView();
  } else {
    fileGrid.style.display = 'none';
    fileList.style.display = 'block';
    renderListView();
  }
}

// Render Grid View
function renderGridView() {
  fileGrid.innerHTML = '';
  filesData.forEach(item => {
    const card = document.createElement('div');
    const isSelected = selectedFileIds.has(item.id);
    card.className = `file-card ${isSelected ? 'selected' : ''}`;
    card.dataset.id = item.id;

    const isStarred = item.starred;
    const isTrash = currentCategory === 'trash';

    card.innerHTML = `
      <div class="card-top-row">
        <div class="card-actions-left">
          ${!isTrash ? `
            <input type="checkbox" class="file-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleSelectFile('${item.id}')">
          ` : `
            <div style="display: flex; gap: 4px;">
              <button class="star-btn" title="Restore" style="color: var(--primary);" onclick="event.stopPropagation(); restoreItem('${item.id}')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
              </button>
              <button class="star-btn" title="Delete Forever" style="color: var(--danger);" onclick="event.stopPropagation(); deletePermanently('${item.id}')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          `}
        </div>
        
        <div style="position: relative;">
          <button class="more-btn" title="More actions" onclick="event.stopPropagation(); toggleContextMenu('${item.id}', this)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="1.5"></circle><circle cx="12" cy="5" r="1.5"></circle><circle cx="12" cy="19" r="1.5"></circle>
            </svg>
          </button>
          <div id="context-menu-${item.id}" class="context-menu">
            ${renderContextMenuItems(item, isTrash)}
          </div>
        </div>
      </div>

      <div class="file-icon" onclick="handleItemClick('${item.id}')">
        ${getIconForType(item.type, 48)}
      </div>

      <div class="file-name" title="${escapeHtml(item.name)}" onclick="handleItemClick('${item.id}')">
        ${escapeHtml(item.name)}
      </div>

      <div class="file-meta">
        <span>${escapeHtml(item.size_formatted)}</span>
        <span>${escapeHtml(item.date_formatted)}</span>
      </div>
    `;

    fileGrid.appendChild(card);
  });
}

// Render List View
function renderListView() {
  const isTrash = currentCategory === 'trash';
  let html = `
    <table class="file-list-table">
      <thead>
        <tr>
          <th style="width: 40px;">
            ${!isTrash ? `<input type="checkbox" onchange="toggleSelectAll(this.checked)">` : ''}
          </th>
          <th>Name</th>
          <th>Size</th>
          <th>Date Modified</th>
          <th style="text-align: right;">Actions</th>
        </tr>
      </thead>
      <tbody>
  `;

  filesData.forEach(item => {
    const isStarred = item.starred;
    const isSelected = selectedFileIds.has(item.id);
    html += `
      <tr class="${isSelected ? 'selected' : ''}" onclick="handleItemClick('${item.id}')">
        <td onclick="event.stopPropagation();">
          ${!isTrash ? `<input type="checkbox" class="file-checkbox" ${isSelected ? 'checked' : ''} onchange="toggleSelectFile('${item.id}')">` : ''}
        </td>
        <td>
          <div class="list-file-cell">
            <div class="list-file-icon">${getIconForType(item.type, 24)}</div>
            <span style="font-weight: 500;">${escapeHtml(item.name)}</span>
          </div>
        </td>
        <td>${escapeHtml(item.size_formatted)}</td>
        <td>${escapeHtml(item.date_formatted)}</td>
        <td style="text-align: right;" onclick="event.stopPropagation();">
          <div style="position: relative; display: inline-block;">
            <button class="more-btn" style="opacity: 1;" onclick="toggleContextMenu('${item.id}', this)">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="1.5"></circle><circle cx="12" cy="5" r="1.5"></circle><circle cx="12" cy="19" r="1.5"></circle>
              </svg>
            </button>
            <div id="context-menu-${item.id}" class="context-menu">
              ${renderContextMenuItems(item, isTrash)}
            </div>
          </div>
        </td>
      </tr>
    `;
  });

  html += `</tbody></table>`;
  fileList.innerHTML = html;
}

// Item Click Handler (Open Folder or Open Preview)
function handleItemClick(id) {
  const item = filesData.find(f => f.id === id);
  if (!item) return;

  if (item.is_folder) {
    navigateToFolder(item.id, item.name);
  } else {
    openItemPreview(id);
  }
}

// Multi-Selection
function toggleSelectFile(id) {
  if (selectedFileIds.has(id)) {
    selectedFileIds.delete(id);
  } else {
    selectedFileIds.add(id);
  }
  updateBatchUI();
  renderFiles();
}

function toggleSelectAll(checked) {
  if (checked) {
    filesData.forEach(f => selectedFileIds.add(f.id));
  } else {
    selectedFileIds.clear();
  }
  updateBatchUI();
  renderFiles();
}

function clearSelection() {
  selectedFileIds.clear();
  updateBatchUI();
  renderFiles();
}

function updateBatchUI() {
  const count = selectedFileIds.size;
  if (count > 0) {
    batchBar.classList.add('active');
    batchCountText.textContent = `${count} selected`;
  } else {
    batchBar.classList.remove('active');
  }
}

// Batch Actions
async function batchDownloadZip() {
  if (selectedFileIds.size === 0) return;
  showToast('Preparing ZIP archive...');
  try {
    const res = await fetch('/api/files/download-zip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: Array.from(selectedFileIds) })
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `IntelliDrive_Selection_${Date.now()}.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    clearSelection();
  } catch (err) {
    console.error('Batch download error:', err);
  }
}

async function batchMoveToTrash() {
  if (selectedFileIds.size === 0) return;
  const ids = Array.from(selectedFileIds);
  for (const id of ids) {
    await fetch(`/api/files/${id}/delete`, { method: 'POST' });
  }
  clearSelection();
  showToast('Moved selected items to Trash');
  fetchFiles();
}

// Context Menu Content
function renderContextMenuItems(item, isTrash) {
  if (isTrash) {
    return `
      <button class="dropdown-item" onclick="event.stopPropagation(); restoreItem('${item.id}')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
        Restore
      </button>
      <div class="dropdown-divider"></div>
      <button class="dropdown-item text-danger" onclick="event.stopPropagation(); deletePermanently('${item.id}')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        Delete Forever
      </button>
    `;
  }

  return `
    <button class="dropdown-item" onclick="event.stopPropagation(); openItemPreview('${item.id}')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
      Preview / Details
    </button>
    ${!item.is_folder && item.saved_name ? `
      <a class="dropdown-item" href="/api/download/${item.id}" download onclick="event.stopPropagation(); closeAllContextMenus();">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
        Download
      </a>
    ` : ''}
    <div class="dropdown-divider"></div>
    <button class="dropdown-item text-danger" onclick="event.stopPropagation(); moveToTrash('${item.id}')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
      Delete
    </button>
  `;
}

// Toggle Context Menu
function toggleContextMenu(id, btnElement) {
  const menu = document.getElementById(`context-menu-${id}`);
  if (!menu) return;

  const isOpen = menu.classList.contains('open');
  closeAllContextMenus();

  if (!isOpen) {
    menu.classList.add('open');
    activeContextMenu = menu;
  }
}

function closeAllContextMenus() {
  document.querySelectorAll('.context-menu').forEach(m => m.classList.remove('open'));
  activeContextMenu = null;
}

// Item Actions
async function toggleStar(id) {
  closeAllContextMenus();
  try {
    const res = await fetch(`/api/files/${id}/star`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      const item = filesData.find(f => f.id === id);
      if (item) item.starred = data.starred;
      if (currentCategory === 'starred' && !data.starred) {
        filesData = filesData.filter(f => f.id !== id);
      }
      renderFiles();
    }
  } catch (err) {
    console.error('Error starring item:', err);
  }
}

async function moveToTrash(id) {
  closeAllContextMenus();
  try {
    const res = await fetch(`/api/files/${id}/delete`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      filesData = filesData.filter(f => f.id !== id);
      renderFiles();
      showToast('Item moved to Trash');
      fetchFiles();
    }
  } catch (err) {
    console.error('Error deleting item:', err);
  }
}

async function restoreItem(id) {
  closeAllContextMenus();
  try {
    const res = await fetch(`/api/files/${id}/restore`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      filesData = filesData.filter(f => f.id !== id);
      renderFiles();
      showToast('Item restored');
      fetchFiles();
    }
  } catch (err) {
    console.error('Error restoring item:', err);
  }
}

async function deletePermanently(id) {
  closeAllContextMenus();
  filesData = filesData.filter(f => f.id !== id);
  renderFiles();
  showToast('Item permanently deleted');

  try {
    await fetch(`/api/files/${id}/delete?permanent=true`, { method: 'POST' });
    fetchFiles();
  } catch (err) {
    console.error('Error deleting item:', err);
    fetchFiles();
  }
}

async function emptyTrash() {
  closeAllContextMenus();
  filesData = [];
  renderFiles();
  showToast('Trash emptied');

  try {
    await fetch('/api/files/empty-trash', { method: 'POST' });
    fetchFiles();
  } catch (err) {
    console.error('Error emptying trash:', err);
    fetchFiles();
  }
}

// Rich File Preview Modal
async function openItemPreview(id) {
  closeAllContextMenus();
  const item = filesData.find(f => f.id === id);
  if (!item) return;

  previewModalTitle.textContent = item.name;

  let bodyContent = `
    <div style="display: flex; flex-direction: column; align-items: center; gap: 1rem; width: 100%;">
      <div style="padding: 1.25rem; background-color: var(--hover-bg); border-radius: var(--radius-lg); display: flex; justify-content: center; align-items: center; width: 100%; min-height: 180px;">
  `;

  if (item.type === 'image' && item.saved_name) {
    bodyContent += `<img src="/static/uploads/${item.saved_name}" alt="${escapeHtml(item.name)}" style="max-width: 100%; max-height: 340px; border-radius: 8px; object-fit: contain;">`;
  } else if (item.type === 'video' && item.saved_name) {
    bodyContent += `<video src="/api/view/${item.id}" controls style="max-width: 100%; max-height: 320px; border-radius: 8px;"></video>`;
  } else if (item.type === 'audio' && item.saved_name) {
    bodyContent += `<audio src="/api/view/${item.id}" controls style="width: 100%;"></audio>`;
  } else if (item.type === 'pdf' && item.saved_name) {
    bodyContent += `<iframe src="/api/view/${item.id}" style="width: 100%; height: 360px; border: none; border-radius: 8px;"></iframe>`;
  } else if (['code', 'document'].includes(item.type) && item.saved_name) {
    bodyContent += `<div id="code-content-box" class="code-preview-container">Loading contents...</div>`;
    fetchTextPreview(item.id);
  } else {
    bodyContent += getIconForType(item.type, 72);
  }

  bodyContent += `
      </div>
      <div style="width: 100%; background-color: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1rem; font-size: 0.875rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
          <span style="color: var(--text-secondary);">Type:</span>
          <span style="font-weight: 500; text-transform: uppercase;">${escapeHtml(item.type)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
          <span style="color: var(--text-secondary);">Size:</span>
          <span style="font-weight: 500;">${escapeHtml(item.size_formatted)}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: var(--text-secondary);">Modified:</span>
          <span style="font-weight: 500;">${escapeHtml(item.date_formatted)}</span>
        </div>
      </div>
    </div>
  `;

  previewModalBody.innerHTML = bodyContent;
  openModal(previewModal);
}

async function fetchTextPreview(id) {
  try {
    const res = await fetch(`/api/view/${id}`);
    const text = await res.text();
    const box = document.getElementById('code-content-box');
    if (box) box.textContent = text;
  } catch (e) {
    const box = document.getElementById('code-content-box');
    if (box) box.textContent = 'Unable to render preview.';
  }
}

// Share Modal
async function openShareModal(id) {
  closeAllContextMenus();
  const item = filesData.find(f => f.id === id);
  if (!item) return;

  shareModalTitle.textContent = `Share "${item.name}"`;
  shareLinkInput.value = 'Generating secure link...';
  openModal(shareModal);

  try {
    const res = await fetch(`/api/files/${id}/share`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      shareLinkInput.value = data.share_url;
    }
  } catch (err) {
    shareLinkInput.value = 'Error generating link';
  }
}

function copyShareLink() {
  shareLinkInput.select();
  navigator.clipboard.writeText(shareLinkInput.value);
  showToast('Link copied to clipboard!');
}

// File Upload Handler
uploadBtn.addEventListener('click', () => {
  fileInput.click();
});

fileInput.addEventListener('change', (e) => {
  const files = e.target.files;
  if (files && files.length > 0) {
    handleFileUpload(files);
  }
  fileInput.value = '';
});

// Drag & Drop
['dragenter', 'dragover'].forEach(eventName => {
  document.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzoneOverlay.classList.add('active');
  });
});

['dragleave', 'drop'].forEach(eventName => {
  dropzoneOverlay.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (eventName === 'drop') {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFileUpload(files);
      }
    }
    dropzoneOverlay.classList.remove('active');
  });
});

async function handleFileUpload(files) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  if (currentFolderId) {
    formData.append('parent_id', currentFolderId);
  }

  const toast = createUploadToast(files.length === 1 ? files[0].name : `${files.length} files`);

  try {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload', true);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        updateUploadToast(toast, percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        completeUploadToast(toast, true, 'Upload completed');
        fetchFiles();
      } else {
        completeUploadToast(toast, false, 'Upload failed');
      }
    };

    xhr.onerror = () => {
      completeUploadToast(toast, false, 'Upload error');
    };

    xhr.send(formData);
  } catch (err) {
    console.error('Upload error:', err);
    completeUploadToast(toast, false, 'Upload error');
  }
}

// Toast Helpers
function createUploadToast(title) {
  const toast = document.createElement('div');
  toast.className = 'upload-toast';
  toast.innerHTML = `
    <div class="upload-toast-header">
      <span class="upload-toast-filename">${escapeHtml(title)}</span>
      <span class="upload-toast-percent" style="color: var(--primary);">0%</span>
    </div>
    <div class="upload-toast-progress-bar">
      <div class="upload-toast-progress-fill"></div>
    </div>
  `;
  uploadToastContainer.appendChild(toast);
  return toast;
}

function updateUploadToast(toast, percent) {
  const fill = toast.querySelector('.upload-toast-progress-fill');
  const percentText = toast.querySelector('.upload-toast-percent');
  if (fill) fill.style.width = `${percent}%`;
  if (percentText) percentText.textContent = `${percent}%`;
}

function completeUploadToast(toast, success, message) {
  const fill = toast.querySelector('.upload-toast-progress-fill');
  const percentText = toast.querySelector('.upload-toast-percent');
  if (fill) {
    fill.style.width = '100%';
    fill.style.backgroundColor = success ? 'var(--success)' : 'var(--danger)';
  }
  if (percentText) {
    percentText.textContent = message;
    percentText.style.color = success ? 'var(--success)' : 'var(--danger)';
  }
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.4s ease';
    setTimeout(() => toast.remove(), 400);
  }, 3000);
}

function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'upload-toast';
  toast.innerHTML = `
    <div class="upload-toast-header">
      <span style="color: var(--text-main); font-weight: 500;">${escapeHtml(message)}</span>
      <span style="color: var(--success);">✓</span>
    </div>
  `;
  uploadToastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.4s ease';
    setTimeout(() => toast.remove(), 400);
  }, 2500);
}

// Create New Folder
newFolderBtn.addEventListener('click', () => {
  newFolderNameInput.value = '';
  openModal(newFolderModal);
  setTimeout(() => newFolderNameInput.focus(), 100);
});

createFolderConfirmBtn.addEventListener('click', async () => {
  const folderName = newFolderNameInput.value.trim() || 'New Folder';
  try {
    const res = await fetch('/api/folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: folderName, parent_id: currentFolderId })
    });
    const data = await res.json();
    if (data.success) {
      closeModal(newFolderModal);
      showToast(`Created folder "${folderName}"`);
      fetchFiles();
    }
  } catch (err) {
    console.error('Error creating folder:', err);
  }
});

// View Toggle
gridViewBtn.addEventListener('click', () => {
  currentView = 'grid';
  gridViewBtn.classList.add('active');
  listViewBtn.classList.remove('active');
  renderFiles();
});

listViewBtn.addEventListener('click', () => {
  currentView = 'list';
  listViewBtn.classList.add('active');
  gridViewBtn.classList.remove('active');
  renderFiles();
});

// Filter Chips
document.querySelectorAll('.filter-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    currentTypeFilter = chip.dataset.type;
    fetchFiles();
  });
});

// Sort Select
if (sortSelect) {
  sortSelect.addEventListener('change', (e) => {
    currentSort = e.target.value;
    fetchFiles();
  });
}

// Sidebar Navigation
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', (e) => {
    const cat = item.dataset.category;
    if (!cat) return;

    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    item.classList.add('active');

    currentCategory = cat;
    currentFolderId = null;
    clearSelection();

    closeMobileSidebar();
    fetchFiles();
  });
});

// Search functionality
searchInput.addEventListener('input', (e) => {
  searchQuery = e.target.value;
  if (searchQuery.length > 0) {
    searchClearBtn.classList.add('visible');
  } else {
    searchClearBtn.classList.remove('visible');
  }
  fetchFiles();
});

searchClearBtn.addEventListener('click', () => {
  searchInput.value = '';
  searchQuery = '';
  searchClearBtn.classList.remove('visible');
  fetchFiles();
  searchInput.focus();
});

// User Profile Menu
profileBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  profileDropdown.classList.toggle('open');
  profileBtn.classList.toggle('active');
});

// Dark Mode Toggle
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const target = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', target);
  localStorage.setItem('theme', target);
  const themeText = document.getElementById('theme-toggle-text');
  if (themeText) themeText.textContent = target === 'dark' ? 'Light Mode' : 'Dark Mode';
}

// Modals Handling
function openModal(modal) {
  modal.classList.add('open');
}

function closeModal(modal) {
  modal.classList.remove('open');
}

document.querySelectorAll('.modal-close-trigger').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const modal = e.target.closest('.modal-backdrop');
    if (modal) closeModal(modal);
  });
});

document.querySelectorAll('.modal-backdrop').forEach(m => {
  m.addEventListener('click', (e) => {
    if (e.target === m) closeModal(m);
  });
});

// Mobile Sidebar
hamburgerBtn.addEventListener('click', () => {
  sidebar.classList.add('mobile-open');
  sidebarOverlay.classList.add('active');
});

function closeMobileSidebar() {
  sidebar.classList.remove('mobile-open');
  sidebarOverlay.classList.remove('active');
}

if (sidebarCloseBtn) sidebarCloseBtn.addEventListener('click', closeMobileSidebar);
if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeMobileSidebar);

// Global Click Close
document.addEventListener('click', (e) => {
  if (profileDropdown && !profileDropdown.contains(e.target) && e.target !== profileBtn) {
    profileDropdown.classList.remove('open');
    profileBtn.classList.remove('active');
  }
  if (activeContextMenu && !activeContextMenu.contains(e.target)) {
    closeAllContextMenus();
  }
});

// Escape HTML Helper
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  const themeText = document.getElementById('theme-toggle-text');
  if (themeText) themeText.textContent = savedTheme === 'dark' ? 'Light Mode' : 'Dark Mode';

  fetchFiles();
});
