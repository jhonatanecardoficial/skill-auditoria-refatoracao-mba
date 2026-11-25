/**
 * Módulo de utilitários e compatibilidade retroativa.
 * Fornece cache em memória com limite de tamanho (Bounded Cache) para evitar vazamento de memória.
 */

const config = require('./config/config');
const { hashPassword } = require('./services/security.service');

const MAX_CACHE_SIZE = 500;
class BoundedCache {
  constructor(limit = MAX_CACHE_SIZE) {
    this.limit = limit;
    this.map = new Map();
  }

  set(key, value) {
    if (this.map.size >= this.limit) {
      const oldestKey = this.map.keys().next().value;
      this.map.delete(oldestKey);
    }
    this.map.set(key, value);
  }

  get(key) {
    return this.map.get(key);
  }

  has(key) {
    return this.map.has(key);
  }

  get size() {
    return this.map.size;
  }
}

const globalCache = new BoundedCache();
let totalRevenue = 0;

function logAndCache(key, data) {
  globalCache.set(key, data);
}

function badCrypto(pwd) {
  // Utiliza hash seguro por debaixo dos panos mantendo a assinatura esperada
  return hashPassword(pwd).substring(0, 16);
}

module.exports = {
  config,
  logAndCache,
  badCrypto,
  globalCache,
  totalRevenue,
  BoundedCache
};
