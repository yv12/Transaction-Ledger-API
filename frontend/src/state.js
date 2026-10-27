/**
 * Application State & Role-Based Access Control
 */

import { api } from './api.js';

export const ROLES = {
  ADMIN: 'admin',
  USER: 'user',
};

class Store {
  constructor() {
    this.role = localStorage.getItem('aether_role') || ROLES.ADMIN;
    this.currentAccountId = localStorage.getItem('aether_user_account_id') || null;
    this.accounts = [];
    this.isBackendOnline = false;
    this.listeners = new Set();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    for (const listener of this.listeners) {
      listener(this);
    }
  }

  setRole(newRole) {
    if (newRole !== ROLES.ADMIN && newRole !== ROLES.USER) return;
    this.role = newRole;
    localStorage.setItem('aether_role', newRole);
    this.notify();
  }

  setCurrentAccountId(id) {
    this.currentAccountId = id;
    if (id) {
      localStorage.setItem('aether_user_account_id', id);
    } else {
      localStorage.removeItem('aether_user_account_id');
    }
    this.notify();
  }

  getCurrentAccount() {
    if (!this.currentAccountId) return null;
    return this.accounts.find((a) => a.id === this.currentAccountId) || null;
  }

  async checkHealth() {
    try {
      await api.getHealth();
      this.isBackendOnline = true;
    } catch {
      this.isBackendOnline = false;
    }
    this.notify();
    return this.isBackendOnline;
  }

  async refreshAccounts() {
    try {
      const data = await api.getAccounts();
      this.accounts = Array.isArray(data) ? data : [];
      this.isBackendOnline = true;

      // If in user mode and current account is invalid or not set, default to first available
      if (this.role === ROLES.USER) {
        if (!this.currentAccountId && this.accounts.length > 0) {
          this.setCurrentAccountId(this.accounts[0].id);
        } else if (this.currentAccountId && !this.accounts.some((a) => a.id === this.currentAccountId)) {
          if (this.accounts.length > 0) {
            this.setCurrentAccountId(this.accounts[0].id);
          } else {
            this.setCurrentAccountId(null);
          }
        }
      }
    } catch (err) {
      this.isBackendOnline = false;
      throw err;
    } finally {
      this.notify();
    }
    return this.accounts;
  }
}

export const store = new Store();

export function generateReference(prefix = 'TX') {
  const ts = Date.now().toString(36).toUpperCase();
  const rand = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `${prefix}-${ts}-${rand}`;
}
