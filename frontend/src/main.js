/**
 * Aether Ledger Frontend Application
 * Unified Role-Based Access Control (Admin & Account Holder)
 */

import { api, getApiBaseUrl, setApiBaseUrl } from './api.js';
import { store, ROLES, generateReference } from './state.js';

// DOM Elements
const elements = {
  // Roles
  roleAdminBtn: document.getElementById('role-admin-btn'),
  roleUserBtn: document.getElementById('role-user-btn'),
  viewAdmin: document.getElementById('view-admin'),
  viewUser: document.getElementById('view-user'),
  activeUserBadge: document.getElementById('active-user-badge'),
  headerUserName: document.getElementById('header-user-name'),
  headerUserAvatar: document.getElementById('header-user-avatar'),

  // Backend Status
  backendPulse: document.getElementById('backend-pulse'),
  backendStatusText: document.getElementById('backend-status-text'),
  backendStatusPill: document.getElementById('backend-status-pill'),
  offlineBanner: document.getElementById('offline-banner'),
  offlineUrlText: document.getElementById('offline-url-text'),
  retryConnectionBtn: document.getElementById('retry-connection-btn'),

  // Admin View
  statTotalDeposits: document.getElementById('stat-total-deposits'),
  statTotalAccounts: document.getElementById('stat-total-accounts'),
  adminAccountsTbody: document.getElementById('admin-accounts-tbody'),
  adminSearchInput: document.getElementById('admin-search-input'),
  adminRefreshAccountsBtn: document.getElementById('admin-refresh-accounts-btn'),
  adminNewAccountBtn: document.getElementById('admin-new-account-btn'),
  adminTransferBtn: document.getElementById('admin-transfer-btn'),

  // User View
  userActiveLayout: document.getElementById('user-active-layout'),
  userNoAccountState: document.getElementById('user-no-account-state'),
  userSelectProfileBtn: document.getElementById('user-select-profile-btn'),
  userGotoAdminBtn: document.getElementById('user-goto-admin-btn'),
  userCardBalance: document.getElementById('user-card-balance'),
  userCardName: document.getElementById('user-card-name'),
  userCardId: document.getElementById('user-card-id'),
  userRefreshBalanceBtn: document.getElementById('user-refresh-balance-btn'),
  userTransferBtn: document.getElementById('user-transfer-btn'),
  userQuickDownloadBtn: document.getElementById('user-quick-download-btn'),
  txFeedList: document.getElementById('tx-feed-list'),
  txTotalCount: document.getElementById('tx-total-count'),
  paginationControls: document.getElementById('pagination-controls'),
  paginationPrevBtn: document.getElementById('pagination-prev-btn'),
  paginationNextBtn: document.getElementById('pagination-next-btn'),
  paginationPageInfo: document.getElementById('pagination-page-info'),

  // Indian Bank Filter & Summary Elements
  btnToggleFilters: document.getElementById('btn-toggle-filters'),
  filterBtnText: document.getElementById('filter-btn-text'),
  filterActiveBadge: document.getElementById('filter-active-badge'),
  bankFilterCard: document.getElementById('bank-filter-card'),
  btnCloseFilterCard: document.getElementById('btn-close-filter-card'),
  filterFromDate: document.getElementById('filter-from-date'),
  filterToDate: document.getElementById('filter-to-date'),
  filterMinAmount: document.getElementById('filter-min-amount'),
  filterMaxAmount: document.getElementById('filter-max-amount'),
  filterSearchInput: document.getElementById('filter-search-input'),
  btnApplyFilters: document.getElementById('btn-apply-filters'),
  btnResetFilters: document.getElementById('btn-reset-filters'),
  btnDownloadCsv: document.getElementById('btn-download-csv'),
  summaryTotalCredits: document.getElementById('summary-total-credits'),
  summaryTotalDebits: document.getElementById('summary-total-debits'),
  summaryNetFlow: document.getElementById('summary-net-flow'),
  summaryRecordCount: document.getElementById('summary-record-count'),

  // Modals
  modalCreateAccount: document.getElementById('modal-create-account'),
  formCreateAccount: document.getElementById('form-create-account'),
  newAccountName: document.getElementById('new-account-name'),

  modalTransfer: document.getElementById('modal-transfer'),
  formTransfer: document.getElementById('form-transfer'),
  transferModalTitle: document.getElementById('transfer-modal-title'),
  transferFromSelect: document.getElementById('transfer-from-select'),
  transferToSelect: document.getElementById('transfer-to-select'),
  transferAmount: document.getElementById('transfer-amount'),
  transferDesc: document.getElementById('transfer-desc'),

  modalTransaction: document.getElementById('modal-transaction'),
  formTransaction: document.getElementById('form-transaction'),
  txAccountId: document.getElementById('tx-account-id'),
  txAccountNameBadge: document.getElementById('tx-account-name-badge'),
  txTypeSelect: document.getElementById('tx-type-select'),
  txAmount: document.getElementById('tx-amount'),
  txDescription: document.getElementById('tx-description'),

  modalSelectAccount: document.getElementById('modal-select-account'),
  accountSelectionList: document.getElementById('account-selection-list'),
  modalSelectCreateNewBtn: document.getElementById('modal-select-create-new-btn'),

  modalApiSettings: document.getElementById('modal-api-settings'),
  formApiSettings: document.getElementById('form-api-settings'),
  apiUrlInput: document.getElementById('api-url-input'),

  // Admin Global Transactions
  adminGlobalTxTbody: document.getElementById('admin-global-tx-tbody'),
  adminTxSearch: document.getElementById('admin-tx-search'),
  adminRefreshTxBtn: document.getElementById('admin-refresh-tx-btn'),
  adminTxTotalCount: document.getElementById('admin-tx-total-count'),
  adminTxPrevBtn: document.getElementById('admin-tx-prev-btn'),
  adminTxNextBtn: document.getElementById('admin-tx-next-btn'),
  adminTxPageIndicator: document.getElementById('admin-tx-page-indicator'),
  adminTxFilterAll: document.getElementById('admin-tx-filter-all'),
  adminTxFilterCredit: document.getElementById('admin-tx-filter-credit'),
  adminTxFilterDebit: document.getElementById('admin-tx-filter-debit'),

  // Admin Statement Modal
  modalAdminStatement: document.getElementById('modal-admin-statement'),
  statementModalTitle: document.getElementById('statement-modal-title'),
  statementModalSubtitle: document.getElementById('statement-modal-subtitle'),
  modalStmtBalance: document.getElementById('modal-stmt-balance'),
  modalStmtTbody: document.getElementById('modal-stmt-tbody'),
  modalStmtTotal: document.getElementById('modal-stmt-total'),
  modalStmtFilterAll: document.getElementById('modal-stmt-filter-all'),
  modalStmtFilterCredit: document.getElementById('modal-stmt-filter-credit'),
  modalStmtFilterDebit: document.getElementById('modal-stmt-filter-debit'),

  // Admin Workspace Tabs & Parallel Grid
  adminTabParallel: document.getElementById('admin-tab-parallel'),
  adminTabAccounts: document.getElementById('admin-tab-accounts'),
  adminTabTransactions: document.getElementById('admin-tab-transactions'),
  adminParallelContainer: document.getElementById('admin-parallel-container'),
  adminAccountsCountBadge: document.getElementById('admin-accounts-count-badge'),
  adminLiveToggleBtn: document.getElementById('admin-live-toggle-btn'),
  adminLiveText: document.getElementById('admin-live-text'),
  adminLiveLastSync: document.getElementById('admin-live-last-sync'),

  toastContainer: document.getElementById('toast-container'),
};

// Application State for User Pagination & Filter
let currentTxFilter = '';
let currentTxPage = 1;
const TX_LIMIT = 10;
let lastPaginationData = null;

// Application State for Admin Transactions & Statement Modal
let adminTxFilter = '';
let adminTxPage = 1;
const ADMIN_TX_LIMIT = 10;
let lastAdminPaginationData = null;

let modalStmtAccountId = null;
let modalStmtFilter = '';

// Live Auto-Refresh State
let adminLivePaused = false;
let adminLatestTxId = null;
let adminPollInterval = null;


// ==========================================
// TOAST SYSTEM
// ==========================================
function showToast({ title, message, type = 'success', duration = 4000 }) {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const iconSvg = type === 'success'
    ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`
    : `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;

  toast.innerHTML = `
    <div class="toast-icon">${iconSvg}</div>
    <div class="toast-content">
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    </div>
  `;

  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

// ==========================================
// MODAL CONTROLS
// ==========================================
function openModal(modal) {
  if (!modal) return;
  modal.classList.add('open');
}

function closeModal(modal) {
  if (!modal) return;
  modal.classList.remove('open');
}

document.querySelectorAll('[data-close-modal]').forEach((btn) => {
  btn.addEventListener('click', () => {
    const backdrop = btn.closest('.modal-backdrop');
    closeModal(backdrop);
  });
});

window.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    closeModal(e.target);
  }
});

// ==========================================
// FORMATTERS & HELPERS (INDIAN BANKING STANDARDS)
// ==========================================
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(amount || 0);
}

function formatDate(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ==========================================
// ROLE-BASED ACCESS CONTROL
// ==========================================
function updateRoleUI() {
  const isAdmin = store.role === ROLES.ADMIN;

  // Toggle Header Buttons
  elements.roleAdminBtn.classList.toggle('active', isAdmin);
  elements.roleAdminBtn.setAttribute('aria-selected', String(isAdmin));

  elements.roleUserBtn.classList.toggle('active', !isAdmin);
  elements.roleUserBtn.setAttribute('aria-selected', String(!isAdmin));

  // Toggle View Panels
  elements.viewAdmin.style.display = isAdmin ? 'block' : 'none';
  elements.viewUser.style.display = isAdmin ? 'none' : 'block';

  // Active User Badge in Header
  const currentAcc = store.getCurrentAccount();
  if (!isAdmin && currentAcc) {
    elements.activeUserBadge.style.display = 'flex';
    elements.headerUserName.textContent = currentAcc.name;
    elements.headerUserAvatar.textContent = (currentAcc.name || 'U').charAt(0).toUpperCase();
  } else {
    elements.activeUserBadge.style.display = 'none';
  }

  // Render view-specific content
  if (isAdmin) {
    renderAdminView();
  } else {
    renderUserView();
  }
}

// ==========================================
// ADMIN VIEW
// ==========================================
function renderAdminView() {
  renderAdminTable();
  loadAdminGlobalTransactions();
}

function renderAdminTable() {
  const accounts = store.accounts;
  const searchTerm = (elements.adminSearchInput.value || '').toLowerCase().trim();

  const filtered = accounts.filter((acc) => {
    return (
      acc.name.toLowerCase().includes(searchTerm) ||
      acc.id.toLowerCase().includes(searchTerm)
    );
  });

  // Calculate Metrics
  const totalDeposits = accounts.reduce((acc, curr) => acc + (Number(curr.balance) || 0), 0);
  elements.statTotalDeposits.textContent = formatCurrency(totalDeposits);
  elements.statTotalAccounts.textContent = accounts.length.toLocaleString();
  if (elements.adminAccountsCountBadge) {
    elements.adminAccountsCountBadge.textContent = `${filtered.length} Account${filtered.length === 1 ? '' : 's'}`;
  }

  // Render Table
  if (filtered.length === 0) {
    elements.adminAccountsTbody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          ${accounts.length === 0 ? 'No accounts in ledger yet. Create an account to begin.' : 'No accounts match your search query.'}
        </td>
      </tr>
    `;
    return;
  }

  elements.adminAccountsTbody.innerHTML = filtered
    .map((acc) => {
      return `
        <tr data-account-id="${acc.id}">
          <td>
            <div style="font-weight: 700; color: #fff;">${escapeHtml(acc.name)}</div>
          </td>
          <td>
            <span class="account-id-badge" title="Click to copy Account ID" data-copy-id="${acc.id}">
              ${acc.id.substring(0, 8)}...${acc.id.substring(acc.id.length - 6)}
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
            </span>
          </td>
          <td>
            <span class="balance-amount" style="color: ${acc.balance > 0 ? 'var(--color-credit)' : 'var(--text-main)'};">
              ${formatCurrency(acc.balance)}
            </span>
          </td>
          <td style="color: var(--text-muted); font-size: 0.8rem;">
            ${formatDate(acc.created_at)}
          </td>
          <td style="text-align: right;">
            <div style="display: inline-flex; gap: 0.4rem;">
              <button class="btn btn-secondary btn-sm" data-action="view-statement" data-id="${acc.id}" data-name="${escapeHtml(acc.name)}" data-balance="${acc.balance}" title="View Account Ledger Statement">
                Statement
              </button>
              <button class="btn btn-secondary btn-sm" data-action="post-tx" data-id="${acc.id}" data-name="${escapeHtml(acc.name)}" title="Direct Credit or Debit">
                Adjust
              </button>
              <button class="btn btn-primary btn-sm" data-action="switch-user" data-id="${acc.id}" title="Impersonate & login as this customer">
                Portal &rarr;
              </button>
            </div>
          </td>
        </tr>
      `;
    })
    .join('');

  // Attach Table Event Listeners
  elements.adminAccountsTbody.querySelectorAll('[data-copy-id]').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-copy-id');
      navigator.clipboard.writeText(id);
      showToast({ title: 'Copied', message: `Account ID ${id} copied to clipboard!` });
    });
  });

  elements.adminAccountsTbody.querySelectorAll('[data-action="view-statement"]').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-id');
      const name = el.getAttribute('data-name');
      const bal = Number(el.getAttribute('data-balance')) || 0;
      openAdminStatementModal(id, name, bal);
    });
  });

  elements.adminAccountsTbody.querySelectorAll('[data-action="post-tx"]').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-id');
      const name = el.getAttribute('data-name');
      openPostTxModal(id, name);
    });
  });

  elements.adminAccountsTbody.querySelectorAll('[data-action="switch-user"]').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-id');
      store.setCurrentAccountId(id);
      store.setRole(ROLES.USER);
    });
  });
}

// ==========================================
// ADMIN GLOBAL TRANSACTIONS (LATEST FIRST)
// ==========================================
async function loadAdminGlobalTransactions(silent = false) {
  if (!elements.adminGlobalTxTbody) return;

  if (!silent && !elements.adminGlobalTxTbody.children.length) {
    elements.adminGlobalTxTbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-muted);">
          Loading system-wide transactions...
        </td>
      </tr>
    `;
  }

  try {
    const searchTerm = (elements.adminTxSearch?.value || '').trim();
    const res = await api.getAllTransactions({
      type: adminTxFilter || null,
      page: adminTxPage,
      limit: ADMIN_TX_LIMIT,
      search: searchTerm || null,
    });

    const txs = res.data || [];
    lastAdminPaginationData = res.pagination;

    // Check if new transaction arrived at the top
    const newestTxId = txs.length > 0 ? txs[0].id : null;
    const isNewTx = adminLatestTxId && newestTxId && adminLatestTxId !== newestTxId;
    adminLatestTxId = newestTxId;

    if (elements.adminTxTotalCount) {
      elements.adminTxTotalCount.textContent = `${res.pagination.total_records} transaction${res.pagination.total_records === 1 ? '' : 's'} across all accounts`;
    }

    if (elements.adminTxPageIndicator) {
      elements.adminTxPageIndicator.textContent = `Page ${res.pagination.page} of ${Math.max(1, res.pagination.total_pages)}`;
    }

    if (elements.adminTxPrevBtn) {
      elements.adminTxPrevBtn.disabled = res.pagination.page <= 1;
    }
    if (elements.adminTxNextBtn) {
      elements.adminTxNextBtn.disabled = res.pagination.page >= res.pagination.total_pages;
    }

    if (elements.adminLiveLastSync) {
      const nowTime = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
      elements.adminLiveLastSync.textContent = `Updated ${nowTime}`;
    }

    if (txs.length === 0) {
      elements.adminGlobalTxTbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-muted);">
            No transactions found.
          </td>
        </tr>
      `;
      return;
    }

    elements.adminGlobalTxTbody.innerHTML = txs
      .map((tx, idx) => {
        const isCredit = tx.type === 'credit';
        const isFresh = isNewTx && idx === 0;
        return `
          <tr class="${isFresh ? 'new-row-pulse' : ''}">
            <td>
              <div style="font-weight: 600; color: #fff;">${escapeHtml(tx.account_name || 'Account')}</div>
              <div style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">
                ${tx.account_id ? tx.account_id.substring(0, 8) + '...' + tx.account_id.substring(tx.account_id.length - 4) : ''}
              </div>
            </td>
            <td>
              <span class="tx-type-pill ${isCredit ? 'credit' : 'debit'}">
                ${isCredit ? 'CR • Credit' : 'DR • Debit'}
              </span>
            </td>
            <td>
              <span class="mono" style="font-weight: 700; color: ${isCredit ? 'var(--color-credit)' : 'var(--color-debit)'};">
                ${isCredit ? '+' : '-'}${formatCurrency(tx.amount)}
              </span>
            </td>
            <td>
              <span class="mono" style="font-size: 0.75rem; color: var(--text-secondary); background: rgba(255,255,255,0.04); padding: 2px 6px; border-radius: 4px;">
                ${escapeHtml(tx.reference_id)}
              </span>
            </td>
            <td style="color: var(--text-secondary); max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(tx.description || '')}">
              ${escapeHtml(tx.description || '—')}
            </td>
            <td style="color: var(--text-muted); font-size: 0.8rem; white-space: nowrap;">
              ${formatDate(tx.created_at)}
            </td>
          </tr>
        `;
      })
      .join('');
  } catch (err) {
    if (elements.adminGlobalTxTbody && !silent) {
      elements.adminGlobalTxTbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 2rem; color: var(--color-debit);">
            Failed to load global transactions: ${escapeHtml(err.message)}
          </td>
        </tr>
      `;
    }
  }
}

// ==========================================
// ADMIN STATEMENT MODAL
// ==========================================
async function openAdminStatementModal(accountId, accountName, accountBalance) {
  modalStmtAccountId = accountId;
  modalStmtFilter = '';

  if (elements.statementModalTitle) {
    elements.statementModalTitle.textContent = `${accountName}'s Statement`;
  }
  if (elements.statementModalSubtitle) {
    elements.statementModalSubtitle.textContent = `Account ID: ${accountId}`;
  }
  if (elements.modalStmtBalance) {
    elements.modalStmtBalance.textContent = `Balance: ${formatCurrency(accountBalance)}`;
  }

  [elements.modalStmtFilterAll, elements.modalStmtFilterCredit, elements.modalStmtFilterDebit].forEach((b) => {
    if (b) b.classList.remove('active');
  });
  if (elements.modalStmtFilterAll) elements.modalStmtFilterAll.classList.add('active');

  openModal(elements.modalAdminStatement);
  await refreshAdminStatementList();
}

async function refreshAdminStatementList() {
  if (!modalStmtAccountId || !elements.modalStmtTbody) return;

  elements.modalStmtTbody.innerHTML = `
    <tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading ledger transactions...</td></tr>
  `;

  try {
    const res = await api.getTransactions(modalStmtAccountId, {
      type: modalStmtFilter || null,
      page: 1,
      limit: 50,
    });
    const txs = res.data || [];
    if (elements.modalStmtTotal) {
      elements.modalStmtTotal.textContent = `${res.pagination.total_records} record${res.pagination.total_records === 1 ? '' : 's'}`;
    }

    if (txs.length === 0) {
      elements.modalStmtTbody.innerHTML = `
        <tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-muted);">No transactions recorded for this account.</td></tr>
      `;
      return;
    }

    elements.modalStmtTbody.innerHTML = txs
      .map((tx) => {
        const isCredit = tx.type === 'credit';
        return `
          <tr>
            <td>
              <span class="tx-type-pill ${isCredit ? 'credit' : 'debit'}">
                ${isCredit ? 'CR' : 'DR'}
              </span>
            </td>
            <td>
              <span class="mono" style="font-weight: 700; color: ${isCredit ? 'var(--color-credit)' : 'var(--color-debit)'};">
                ${isCredit ? '+' : '-'}${formatCurrency(tx.amount)}
              </span>
            </td>
            <td>
              <span class="mono" style="font-size: 0.75rem; color: var(--text-secondary);">${escapeHtml(tx.reference_id)}</span>
            </td>
            <td style="color: var(--text-secondary);">${escapeHtml(tx.description || '—')}</td>
            <td style="color: var(--text-muted); font-size: 0.8rem;">${formatDate(tx.created_at)}</td>
          </tr>
        `;
      })
      .join('');
  } catch (err) {
    elements.modalStmtTbody.innerHTML = `
      <tr><td colspan="5" style="text-align: center; color: var(--color-debit); padding: 2rem;">Error: ${escapeHtml(err.message)}</td></tr>
    `;
  }
}


// ==========================================
// USER (ACCOUNT HOLDER) VIEW
// ==========================================
async function renderUserView() {
  const currentAcc = store.getCurrentAccount();

  if (!currentAcc) {
    elements.userNoAccountState.style.display = 'block';
    elements.userActiveLayout.style.display = 'none';
    return;
  }

  elements.userNoAccountState.style.display = 'none';
  elements.userActiveLayout.style.display = 'grid';

  elements.userCardName.textContent = currentAcc.name;
  elements.userCardId.textContent = `ID: ${currentAcc.id}`;
  elements.userCardBalance.textContent = formatCurrency(currentAcc.balance);

  // Fetch updated balance & statement
  await refreshUserBalanceAndStatement(currentAcc.id);
}

async function refreshUserBalanceAndStatement(accountId) {
  try {
    // 1. Fetch Fresh Balance
    const balanceData = await api.getBalance(accountId);
    elements.userCardBalance.textContent = formatCurrency(balanceData.balance);

    // Update in store cache
    const acc = store.accounts.find((a) => a.id === accountId);
    if (acc) acc.balance = balanceData.balance;

    // 2. Fetch Statement History
    await loadStatementFeed(accountId);
  } catch (err) {
    showToast({ title: 'Fetch Error', message: err.message, type: 'error' });
  }
}

async function loadStatementFeed(accountId) {
  elements.txFeedList.innerHTML = `
    <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
      Loading transaction statement...
    </div>
  `;

  const startDate = elements.filterFromDate ? elements.filterFromDate.value : null;
  const endDate = elements.filterToDate ? elements.filterToDate.value : null;
  const minAmount = elements.filterMinAmount ? elements.filterMinAmount.value : null;
  const maxAmount = elements.filterMaxAmount ? elements.filterMaxAmount.value : null;
  const search = elements.filterSearchInput ? elements.filterSearchInput.value : null;

  try {
    const res = await api.getTransactions(accountId, {
      type: currentTxFilter || null,
      page: currentTxPage,
      limit: TX_LIMIT,
      start_date: startDate || null,
      end_date: endDate || null,
      min_amount: minAmount || null,
      max_amount: maxAmount || null,
      search: search || null,
    });

    const txs = res.data || [];
    lastPaginationData = res.pagination;

    elements.txTotalCount.textContent = `${res.pagination.total_records} record${res.pagination.total_records === 1 ? '' : 's'}`;

    // Calculate Financial Movement Summary (Indian Bank Style)
    let totalCredits = 0;
    let totalDebits = 0;
    for (const tx of txs) {
      if (tx.type === 'credit') {
        totalCredits += Number(tx.amount) || 0;
      } else {
        totalDebits += Number(tx.amount) || 0;
      }
    }
    const netFlow = totalCredits - totalDebits;

    if (elements.summaryTotalCredits) elements.summaryTotalCredits.textContent = `+${formatCurrency(totalCredits)}`;
    if (elements.summaryTotalDebits) elements.summaryTotalDebits.textContent = `-${formatCurrency(totalDebits)}`;
    if (elements.summaryNetFlow) {
      elements.summaryNetFlow.textContent = `${netFlow >= 0 ? '+' : ''}${formatCurrency(netFlow)}`;
      elements.summaryNetFlow.style.color = netFlow >= 0 ? 'var(--color-credit)' : 'var(--color-debit)';
    }
    if (elements.summaryRecordCount) elements.summaryRecordCount.textContent = `${res.pagination.total_records}`;

    if (txs.length === 0) {
      elements.txFeedList.innerHTML = `
        <div class="empty-state" style="padding: 2.5rem 1rem;">
          <div class="empty-state-title">No Transactions Found</div>
          <p>No transaction records match the specified date range or filter criteria.</p>
        </div>
      `;
      elements.paginationControls.style.display = 'none';
      return;
    }

    elements.txFeedList.innerHTML = txs
      .map((tx) => {
        const isCredit = tx.type === 'credit';
        const sign = isCredit ? '+' : '-';
        return `
          <div class="tx-item">
            <div class="tx-item-left">
              <div class="tx-icon-wrap ${tx.type}">
                ${
                  isCredit
                    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>`
                    : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>`
                }
              </div>
              <div class="tx-meta">
                <div class="tx-description">${escapeHtml(tx.description || (isCredit ? 'Credit Inflow / Deposit' : 'Debit Outflow / Charge'))}</div>
                <div class="tx-reference">UTR / Ref: ${escapeHtml(tx.reference_id)}</div>
              </div>
            </div>
            <div class="tx-item-right">
              <div class="tx-amount ${tx.type}">${sign}${formatCurrency(tx.amount)}</div>
              <div class="tx-time">${formatDate(tx.created_at)}</div>
            </div>
          </div>
        `;
      })
      .join('');

    // Pagination controls
    if (res.pagination.total_pages > 1) {
      elements.paginationControls.style.display = 'flex';
      elements.paginationPageInfo.textContent = `Page ${res.pagination.page} of ${res.pagination.total_pages}`;
      elements.paginationPrevBtn.disabled = res.pagination.page <= 1;
      elements.paginationNextBtn.disabled = res.pagination.page >= res.pagination.total_pages;
    } else {
      elements.paginationControls.style.display = 'none';
    }
  } catch (err) {
    elements.txFeedList.innerHTML = `
      <div style="color: var(--color-debit); padding: 1.5rem; text-align: center;">
        Failed to load transactions: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

// ==========================================
// MODAL DIALOG PREPARATION & SUBMISSION
// ==========================================

// 1. Direct Transaction (Adjust Balance - ADMIN ONLY)
function openPostTxModal(accountId, accountName) {
  if (store.role !== ROLES.ADMIN) {
    showToast({
      title: 'Access Restricted',
      message: 'Direct ledger adjustments can only be performed by a Bank Administrator.',
      type: 'error',
    });
    return;
  }

  elements.txAccountId.value = accountId;
  elements.txAccountNameBadge.textContent = `${accountName} (${accountId.substring(0, 8)}...)`;
  elements.txAmount.value = '';
  elements.txDescription.value = '';
  openModal(elements.modalTransaction);
}

elements.formTransaction.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (store.role !== ROLES.ADMIN) {
    showToast({ title: 'Access Denied', message: 'Only administrators can post manual adjustments.', type: 'error' });
    return;
  }
  const accountId = elements.txAccountId.value;
  const type = elements.txTypeSelect.value;
  const amount = Number(elements.txAmount.value);
  const description = elements.txDescription.value;

  // Reference ID is generated automatically at transaction execution time
  const reference_id = generateReference(type === 'credit' ? 'DEP' : 'WDL');

  try {
    await api.createTransaction(accountId, { type, amount, description, reference_id });
    showToast({
      title: 'Transaction Posted',
      message: `Successfully posted ${type.toUpperCase()} of ${formatCurrency(amount)}. Reference ID: ${reference_id}`,
      type: 'success',
    });
    closeModal(elements.modalTransaction);
    await store.refreshAccounts();
    loadAdminGlobalTransactions();
  } catch (err) {
    showToast({ title: 'Transaction Failed', message: err.message, type: 'error' });
  }
});

// 2. Transfer Funds Modal
function openTransferModal(defaultFromId = null) {
  const accounts = store.accounts;
  if (accounts.length < 2) {
    showToast({
      title: 'Action Required',
      message: 'You need at least 2 accounts in the system to make a transfer.',
      type: 'error',
    });
    return;
  }

  // Populate From
  elements.transferFromSelect.innerHTML = accounts
    .map((a) => `<option value="${a.id}">${escapeHtml(a.name)} (Balance: ${formatCurrency(a.balance)})</option>`)
    .join('');

  if (store.role === ROLES.USER) {
    // In customer mode: permanently lock source to logged-in user
    const cur = store.getCurrentAccount();
    if (!cur) return;
    elements.transferFromSelect.value = cur.id;
    elements.transferFromSelect.disabled = true;
    if (elements.transferModalTitle) elements.transferModalTitle.textContent = 'Send Money / Transfer';
  } else {
    // In admin mode: super admin can transfer between any accounts
    elements.transferFromSelect.disabled = false;
    if (defaultFromId) elements.transferFromSelect.value = defaultFromId;
    if (elements.transferModalTitle) elements.transferModalTitle.textContent = 'System Inter-Account Transfer';
  }

  // Populate To (filter out source)
  updateTransferToOptions();

  elements.transferAmount.value = '';
  elements.transferDesc.value = '';

  openModal(elements.modalTransfer);
}

function updateTransferToOptions() {
  const fromId = elements.transferFromSelect.value;
  const accounts = store.accounts.filter((a) => a.id !== fromId);
  elements.transferToSelect.innerHTML = accounts
    .map((a) => `<option value="${a.id}">${escapeHtml(a.name)} (ID: ${a.id.substring(0, 8)}...)</option>`)
    .join('');
}

elements.transferFromSelect.addEventListener('change', updateTransferToOptions);

elements.formTransfer.addEventListener('submit', async (e) => {
  e.preventDefault();
  const from_account_id = elements.transferFromSelect.value;
  const to_account_id = elements.transferToSelect.value;
  const amount = Number(elements.transferAmount.value);
  const description = elements.transferDesc.value;

  // Reference ID is generated automatically at transfer execution time
  const reference_id = generateReference('TRF');

  try {
    const res = await api.transfer({
      from_account_id,
      to_account_id,
      amount,
      description,
      reference_id,
    });

    showToast({
      title: 'Transfer Complete',
      message: `Transferred ${formatCurrency(amount)}. Reference ID: ${reference_id} (New balance: ${formatCurrency(res.from_balance)})`,
      type: 'success',
    });

    closeModal(elements.modalTransfer);
    await store.refreshAccounts();
    loadAdminGlobalTransactions();
  } catch (err) {
    showToast({ title: 'Transfer Failed', message: err.message, type: 'error' });
  }
});

// 3. Create Account Modal (ADMIN ONLY)
elements.formCreateAccount.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (store.role !== ROLES.ADMIN) {
    showToast({
      title: 'Access Restricted',
      message: 'Account opening is strictly restricted to Bank Administrators.',
      type: 'error',
    });
    closeModal(elements.modalCreateAccount);
    return;
  }

  const name = elements.newAccountName.value.trim();
  if (!name) return;

  try {
    const newAcc = await api.createAccount(name);
    showToast({
      title: 'Account Created',
      message: `Account created for ${newAcc.name} with ID ${newAcc.id.substring(0, 8)}...`,
      type: 'success',
    });
    closeModal(elements.modalCreateAccount);
    elements.newAccountName.value = '';
    await store.refreshAccounts();
  } catch (err) {
    showToast({ title: 'Creation Failed', message: err.message, type: 'error' });
  }
});

// 4. Switch Account Modal
function openSelectAccountModal() {
  const accounts = store.accounts;
  if (accounts.length === 0) {
    showToast({
      title: 'No Registered Accounts',
      message: 'No bank accounts exist yet. Please ask the Bank Administrator to open an account.',
      type: 'error',
    });
    return;
  }

  elements.accountSelectionList.innerHTML = accounts
    .map((acc) => {
      const isSelected = acc.id === store.currentAccountId;
      return `
        <div class="tx-item" style="cursor: pointer; ${isSelected ? 'border-color: var(--accent-primary);' : ''}" data-pick-id="${acc.id}">
          <div>
            <div style="font-weight: 700; color: #fff;">${escapeHtml(acc.name)}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">ID: ${acc.id}</div>
          </div>
          <div style="font-weight: 700; color: var(--color-credit); font-family: var(--font-mono);">
            ${formatCurrency(acc.balance)}
          </div>
        </div>
      `;
    })
    .join('');

  elements.accountSelectionList.querySelectorAll('[data-pick-id]').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-pick-id');
      store.setCurrentAccountId(id);
      closeModal(elements.modalSelectAccount);
    });
  });

  openModal(elements.modalSelectAccount);
}

// 5. API Settings Modal
elements.formApiSettings.addEventListener('submit', async (e) => {
  e.preventDefault();
  const url = elements.apiUrlInput.value;
  setApiBaseUrl(url);
  closeModal(elements.modalApiSettings);
  showToast({ title: 'Settings Saved', message: `API URL set to ${url}. Connecting...` });
  await checkHealthAndRefresh();
});

// ==========================================
// HEALTH & AUTO REFRESH
// ==========================================
async function checkHealthAndRefresh() {
  elements.offlineUrlText.textContent = getApiBaseUrl();
  elements.apiUrlInput.value = getApiBaseUrl();

  const isOnline = await store.checkHealth();
  if (isOnline) {
    elements.backendPulse.className = 'pulse-dot online';
    elements.backendStatusText.textContent = 'Backend Online';
    elements.offlineBanner.style.display = 'none';
    try {
      await store.refreshAccounts();
    } catch {
      // Handled in store
    }
  } else {
    elements.backendPulse.className = 'pulse-dot offline';
    elements.backendStatusText.textContent = 'Backend Offline';
    elements.offlineBanner.style.display = 'flex';
  }
}

// ==========================================
// EVENT LISTENERS
// ==========================================

// Role Switching
elements.roleAdminBtn.addEventListener('click', () => {
  store.setRole(ROLES.ADMIN);
});

elements.roleUserBtn.addEventListener('click', () => {
  store.setRole(ROLES.USER);
});

// Brand Click
document.getElementById('brand-home-btn').addEventListener('click', () => {
  store.setRole(ROLES.ADMIN);
});

// Admin View Buttons
elements.adminNewAccountBtn.addEventListener('click', () => {
  openModal(elements.modalCreateAccount);
});

elements.adminTransferBtn.addEventListener('click', () => {
  openTransferModal();
});

elements.adminRefreshAccountsBtn.addEventListener('click', async () => {
  try {
    await store.refreshAccounts();
    showToast({ title: 'Refreshed', message: 'Accounts list updated successfully.' });
  } catch (err) {
    showToast({ title: 'Refresh Failed', message: err.message, type: 'error' });
  }
});

elements.adminSearchInput.addEventListener('input', () => {
  renderAdminView();
});

// Customer View Buttons
if (elements.userSelectProfileBtn) {
  elements.userSelectProfileBtn.addEventListener('click', openSelectAccountModal);
}
if (elements.userGotoAdminBtn) {
  elements.userGotoAdminBtn.addEventListener('click', () => store.setRole(ROLES.ADMIN));
}

elements.userRefreshBalanceBtn.addEventListener('click', async () => {
  const cur = store.getCurrentAccount();
  if (cur) {
    await refreshUserBalanceAndStatement(cur.id);
    showToast({ title: 'Balance Refreshed', message: 'Updated to latest ledger balance.' });
  }
});

elements.userTransferBtn.addEventListener('click', () => {
  const cur = store.getCurrentAccount();
  if (cur) {
    openTransferModal(cur.id);
  }
});

if (elements.userQuickDownloadBtn) {
  elements.userQuickDownloadBtn.addEventListener('click', () => {
    if (elements.btnDownloadCsv) elements.btnDownloadCsv.click();
  });
}

// Statement Tabs (All / Credit / Debit)
document.querySelectorAll('.filter-tabs .tab-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-tabs .tab-btn').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    currentTxFilter = btn.getAttribute('data-filter') || '';
    currentTxPage = 1;

    const cur = store.getCurrentAccount();
    if (cur) {
      loadStatementFeed(cur.id);
    }
  });
});

// Helper to update active filter indicator badge on the Filter button
function updateFilterActiveBadge() {
  const hasDate = Boolean((elements.filterFromDate && elements.filterFromDate.value) || (elements.filterToDate && elements.filterToDate.value));
  const hasAmount = Boolean((elements.filterMinAmount && elements.filterMinAmount.value) || (elements.filterMaxAmount && elements.filterMaxAmount.value));
  const hasSearch = Boolean(elements.filterSearchInput && elements.filterSearchInput.value.trim());

  let activeCount = 0;
  if (hasDate) activeCount++;
  if (hasAmount) activeCount++;
  if (hasSearch) activeCount++;

  const isFiltered = activeCount > 0;
  if (elements.filterActiveBadge) {
    elements.filterActiveBadge.style.display = isFiltered ? 'inline-block' : 'none';
    elements.filterActiveBadge.textContent = activeCount > 1 ? `${activeCount} Active` : 'Active';
  }
  if (elements.btnToggleFilters) {
    elements.btnToggleFilters.classList.toggle('filter-btn-active', isFiltered);
  }
}

// Toggle Filter Card Collapse / Expand
function toggleFilterCard(forceState = null) {
  if (!elements.bankFilterCard) return;
  const isCurrentlyOpen = elements.bankFilterCard.classList.contains('open');
  const shouldOpen = forceState !== null ? forceState : !isCurrentlyOpen;

  elements.bankFilterCard.classList.toggle('open', shouldOpen);
  if (elements.filterBtnText) {
    elements.filterBtnText.textContent = shouldOpen ? 'Hide Filters' : 'Filter';
  }
}

if (elements.btnToggleFilters) {
  elements.btnToggleFilters.addEventListener('click', () => toggleFilterCard());
}

if (elements.btnCloseFilterCard) {
  elements.btnCloseFilterCard.addEventListener('click', () => toggleFilterCard(false));
}

// Indian Bank Period Presets (Today, 7 Days, 1 Month, 3 Months, FY, Custom)
document.querySelectorAll('#period-presets .period-pill').forEach((pill) => {
  pill.addEventListener('click', () => {
    document.querySelectorAll('#period-presets .period-pill').forEach((p) => p.classList.remove('active'));
    pill.classList.add('active');
    const period = pill.getAttribute('data-period');

    const now = new Date();
    const toDateStr = now.toISOString().split('T')[0];

    if (period === 'all') {
      elements.filterFromDate.value = '';
      elements.filterToDate.value = '';
    } else if (period === 'today') {
      elements.filterFromDate.value = toDateStr;
      elements.filterToDate.value = toDateStr;
    } else if (period === '7days') {
      const past = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      elements.filterFromDate.value = past.toISOString().split('T')[0];
      elements.filterToDate.value = toDateStr;
    } else if (period === '1month') {
      const past = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      elements.filterFromDate.value = past.toISOString().split('T')[0];
      elements.filterToDate.value = toDateStr;
    } else if (period === '3months') {
      const past = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
      elements.filterFromDate.value = past.toISOString().split('T')[0];
      elements.filterToDate.value = toDateStr;
    } else if (period === 'fy') {
      // Indian Financial Year runs 1 April to 31 March
      const curYear = now.getFullYear();
      const curMonth = now.getMonth(); // 0-indexed (April is 3)
      let fyStartYear = curMonth >= 3 ? curYear : curYear - 1;
      let fyEndYear = fyStartYear + 1;
      elements.filterFromDate.value = `${fyStartYear}-04-01`;
      elements.filterToDate.value = `${fyEndYear}-03-31`;
    } else if (period === 'custom') {
      elements.filterFromDate.focus();
      return; // Do not auto-apply, wait for user to select dates
    }

    updateFilterActiveBadge();
    currentTxPage = 1;
    const cur = store.getCurrentAccount();
    if (cur) loadStatementFeed(cur.id);
  });
});

// Apply Filters Button
if (elements.btnApplyFilters) {
  elements.btnApplyFilters.addEventListener('click', () => {
    updateFilterActiveBadge();
    currentTxPage = 1;
    const cur = store.getCurrentAccount();
    if (cur) loadStatementFeed(cur.id);
  });
}

// Reset Filters Button
if (elements.btnResetFilters) {
  elements.btnResetFilters.addEventListener('click', () => {
    if (elements.filterFromDate) elements.filterFromDate.value = '';
    if (elements.filterToDate) elements.filterToDate.value = '';
    if (elements.filterMinAmount) elements.filterMinAmount.value = '';
    if (elements.filterMaxAmount) elements.filterMaxAmount.value = '';
    if (elements.filterSearchInput) elements.filterSearchInput.value = '';

    document.querySelectorAll('#period-presets .period-pill').forEach((p) => p.classList.remove('active'));
    const allPill = document.querySelector('#period-presets .period-pill[data-period="all"]');
    if (allPill) allPill.classList.add('active');

    updateFilterActiveBadge();
    currentTxPage = 1;
    const cur = store.getCurrentAccount();
    if (cur) loadStatementFeed(cur.id);
    showToast({ title: 'Filters Reset', message: 'Showing complete unfiltered account statement.' });
  });
}

// Download Statement as CSV (Indian Bank Standard)
if (elements.btnDownloadCsv) {
  elements.btnDownloadCsv.addEventListener('click', async () => {
    const cur = store.getCurrentAccount();
    if (!cur) return;

    try {
      const startDate = elements.filterFromDate ? elements.filterFromDate.value : null;
      const endDate = elements.filterToDate ? elements.filterToDate.value : null;
      const minAmount = elements.filterMinAmount ? elements.filterMinAmount.value : null;
      const maxAmount = elements.filterMaxAmount ? elements.filterMaxAmount.value : null;
      const search = elements.filterSearchInput ? elements.filterSearchInput.value : null;

      // Fetch up to 100 records for the export
      const res = await api.getTransactions(cur.id, {
        type: currentTxFilter || null,
        page: 1,
        limit: 100,
        start_date: startDate || null,
        end_date: endDate || null,
        min_amount: minAmount || null,
        max_amount: maxAmount || null,
        search: search || null,
      });

      const txs = res.data || [];
      if (txs.length === 0) {
        showToast({ title: 'Export Empty', message: 'No records to download.', type: 'error' });
        return;
      }

      // Build CSV
      const headers = ['"Transaction Date"','"Type"','"Narration / Description"','"UTR / Reference ID"','"Withdrawal (Dr INR)"','"Deposit (Cr INR)"'];
      const rows = txs.map((t) => {
        const dateStr = `"${formatDate(t.created_at)}"`;
        const typeStr = `"${t.type.toUpperCase()}"`;
        const descStr = `"${(t.description || '').replace(/"/g, '""')}"`;
        const refStr = `"${t.reference_id}"`;
        const drStr = t.type === 'debit' ? `"${t.amount.toFixed(2)}"` : '""';
        const crStr = t.type === 'credit' ? `"${t.amount.toFixed(2)}"` : '""';
        return [dateStr, typeStr, descStr, refStr, drStr, crStr].join(',');
      });

      const csvContent = [
        `"AETHER LEDGER - ACCOUNT STATEMENT"`,
        `"Account Holder:","${cur.name}"`,
        `"Account ID:","${cur.id}"`,
        `"Generated On:","${new Date().toLocaleString('en-IN')}"`,
        `"Currency:","INR (₹)"`,
        '',
        headers.join(','),
        ...rows,
      ].join('\r\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `Statement_${cur.name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      showToast({ title: 'Downloaded', message: 'Account statement CSV downloaded successfully!' });
    } catch (err) {
      showToast({ title: 'Export Failed', message: err.message, type: 'error' });
    }
  });
}

// Statement Pagination
elements.paginationPrevBtn.addEventListener('click', () => {
  if (currentTxPage > 1) {
    currentTxPage--;
    const cur = store.getCurrentAccount();
    if (cur) loadStatementFeed(cur.id);
  }
});

elements.paginationNextBtn.addEventListener('click', () => {
  if (lastPaginationData && currentTxPage < lastPaginationData.total_pages) {
    currentTxPage++;
    const cur = store.getCurrentAccount();
    if (cur) loadStatementFeed(cur.id);
  }
});

// Admin Global Transactions Event Listeners
if (elements.adminRefreshTxBtn) {
  elements.adminRefreshTxBtn.addEventListener('click', () => {
    adminTxPage = 1;
    loadAdminGlobalTransactions();
    showToast({ title: 'Refreshed', message: 'System-wide transactions updated.' });
  });
}

if (elements.adminTxSearch) {
  let searchDebounce = null;
  elements.adminTxSearch.addEventListener('input', () => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      adminTxPage = 1;
      loadAdminGlobalTransactions();
    }, 300);
  });
}

[elements.adminTxFilterAll, elements.adminTxFilterCredit, elements.adminTxFilterDebit].forEach((chip) => {
  if (!chip) return;
  chip.addEventListener('click', () => {
    [elements.adminTxFilterAll, elements.adminTxFilterCredit, elements.adminTxFilterDebit].forEach((c) => {
      if (c) c.classList.remove('active');
    });
    chip.classList.add('active');
    adminTxFilter = chip.getAttribute('data-tx-filter') || '';
    adminTxPage = 1;
    loadAdminGlobalTransactions();
  });
});

if (elements.adminTxPrevBtn) {
  elements.adminTxPrevBtn.addEventListener('click', () => {
    if (adminTxPage > 1) {
      adminTxPage--;
      loadAdminGlobalTransactions();
    }
  });
}

if (elements.adminTxNextBtn) {
  elements.adminTxNextBtn.addEventListener('click', () => {
    if (lastAdminPaginationData && adminTxPage < lastAdminPaginationData.total_pages) {
      adminTxPage++;
      loadAdminGlobalTransactions();
    }
  });
}

// Admin Statement Modal Filter Listeners
[elements.modalStmtFilterAll, elements.modalStmtFilterCredit, elements.modalStmtFilterDebit].forEach((chip) => {
  if (!chip) return;
  chip.addEventListener('click', () => {
    [elements.modalStmtFilterAll, elements.modalStmtFilterCredit, elements.modalStmtFilterDebit].forEach((c) => {
      if (c) c.classList.remove('active');
    });
    chip.classList.add('active');
    modalStmtFilter = chip.getAttribute('data-filter') || '';
    refreshAdminStatementList();
  });
});

// Admin Workspace View Switching (Parallel vs Single Tabs)
function setAdminViewMode(mode) {
  if (!elements.adminParallelContainer) return;

  elements.adminTabParallel?.classList.toggle('active', mode === 'parallel');
  elements.adminTabParallel?.setAttribute('aria-selected', String(mode === 'parallel'));

  elements.adminTabAccounts?.classList.toggle('active', mode === 'accounts');
  elements.adminTabAccounts?.setAttribute('aria-selected', String(mode === 'accounts'));

  elements.adminTabTransactions?.classList.toggle('active', mode === 'transactions');
  elements.adminTabTransactions?.setAttribute('aria-selected', String(mode === 'transactions'));

  elements.adminParallelContainer.classList.remove('view-accounts-only', 'view-transactions-only');
  if (mode === 'accounts') {
    elements.adminParallelContainer.classList.add('view-accounts-only');
  } else if (mode === 'transactions') {
    elements.adminParallelContainer.classList.add('view-transactions-only');
  }
}

if (elements.adminTabParallel) {
  elements.adminTabParallel.addEventListener('click', () => setAdminViewMode('parallel'));
}
if (elements.adminTabAccounts) {
  elements.adminTabAccounts.addEventListener('click', () => setAdminViewMode('accounts'));
}
if (elements.adminTabTransactions) {
  elements.adminTabTransactions.addEventListener('click', () => setAdminViewMode('transactions'));
}

// Live Polling Toggle
if (elements.adminLiveToggleBtn) {
  elements.adminLiveToggleBtn.addEventListener('click', () => {
    adminLivePaused = !adminLivePaused;
    elements.adminLiveToggleBtn.classList.toggle('paused', adminLivePaused);
    if (elements.adminLiveText) {
      elements.adminLiveText.textContent = adminLivePaused ? 'PAUSED' : 'LIVE SYNC';
    }
    showToast({
      title: adminLivePaused ? 'Live Sync Paused' : 'Live Sync Active',
      message: adminLivePaused ? 'Automatic audit stream paused.' : 'Live updates resumed (every 4s).',
      type: 'success',
    });
  });
}

// Live polling ticker function
function startAdminLivePolling() {
  if (adminPollInterval) clearInterval(adminPollInterval);
  adminPollInterval = setInterval(async () => {
    if (store.role === ROLES.ADMIN && !adminLivePaused && store.isBackendOnline) {
      try {
        await loadAdminGlobalTransactions(true);
        await store.refreshAccounts();
      } catch {
        // Silently handled in background
      }
    }
  }, 4000);
}

// Backend pill opens settings
elements.backendStatusPill.addEventListener('click', () => {
  openModal(elements.modalApiSettings);
});

elements.retryConnectionBtn.addEventListener('click', checkHealthAndRefresh);

// Subscribe Store to UI
store.subscribe(() => {
  updateRoleUI();
});

// Initialize App
(async function init() {
  updateRoleUI();
  await checkHealthAndRefresh();
  startAdminLivePolling();

  // Periodic health check every 15s
  setInterval(async () => {
    await store.checkHealth();
  }, 15000);
})();
