/**
 * Aether Ledger API Client
 * Connects to the FastAPI backend at http://127.0.0.1:8000
 */

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';

export function getApiBaseUrl() {
  return localStorage.getItem('aether_api_base_url') || DEFAULT_BASE_URL;
}

export function setApiBaseUrl(url) {
  const cleanUrl = url.trim().replace(/\/+$/, '');
  localStorage.setItem('aether_api_base_url', cleanUrl);
}

async function request(endpoint, options = {}) {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;

  const headers = {
    'Accept': 'application/json',
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let message = 'An unexpected error occurred';
      let code = 'ERROR';

      if (data?.error) {
        code = data.error.code || 'ERROR';
        message = data.error.message || message;
      } else if (data?.detail) {
        if (Array.isArray(data.detail)) {
          message = data.detail.map((err) => `${err.loc?.slice(1).join('.') || 'field'}: ${err.msg}`).join(', ');
        } else {
          message = String(data.detail);
        }
        code = 'VALIDATION_ERROR';
      }

      const error = new Error(message);
      error.code = code;
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      const error = new Error(`Cannot connect to Ledger Backend at ${baseUrl}. Ensure the FastAPI server is running.`);
      error.code = 'NETWORK_ERROR';
      throw error;
    }
    throw err;
  }
}

export const api = {
  // Health
  async getHealth() {
    return request('/health');
  },

  // Accounts
  async getAccounts() {
    return request('/accounts');
  },

  async createAccount(name) {
    return request('/accounts', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  async getBalance(accountId) {
    return request(`/accounts/${encodeURIComponent(accountId)}/balance`);
  },

  // Transactions
  async getTransactions(
    accountId,
    {
      type = null,
      page = 1,
      limit = 10,
      start_date = null,
      end_date = null,
      min_amount = null,
      max_amount = null,
      search = null,
    } = {}
  ) {
    const params = new URLSearchParams();
    if (type) params.set('type', type);
    if (page) params.set('page', String(page));
    if (limit) params.set('limit', String(limit));
    if (start_date) params.set('start_date', start_date);
    if (end_date) params.set('end_date', end_date);
    if (min_amount !== null && min_amount !== undefined && min_amount !== '') {
      params.set('min_amount', String(min_amount));
    }
    if (max_amount !== null && max_amount !== undefined && max_amount !== '') {
      params.set('max_amount', String(max_amount));
    }
    if (search && search.trim()) params.set('search', search.trim());

    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/accounts/${encodeURIComponent(accountId)}/transactions${qs}`);
  },

  async createTransaction(accountId, { type, amount, description = '', reference_id }) {
    return request(`/accounts/${encodeURIComponent(accountId)}/transactions`, {
      method: 'POST',
      body: JSON.stringify({
        type,
        amount: Number(amount),
        description: description.trim(),
        reference_id: reference_id.trim(),
      }),
    });
  },

  // Transfers
  async transfer({ from_account_id, to_account_id, amount, description = '', reference_id }) {
    return request('/transfers', {
      method: 'POST',
      body: JSON.stringify({
        from_account_id,
        to_account_id,
        amount: Number(amount),
        description: description.trim(),
        reference_id: reference_id.trim(),
      }),
    });
  },

  // System-wide transactions (Admin)
  async getAllTransactions({ type, page = 1, limit = 10, search } = {}) {
    const params = new URLSearchParams();
    if (type) params.set('type', type);
    if (page) params.set('page', String(page));
    if (limit) params.set('limit', String(limit));
    if (search && search.trim()) params.set('search', search.trim());

    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/transactions${qs}`);
  },
};

