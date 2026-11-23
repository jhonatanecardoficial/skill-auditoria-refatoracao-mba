/**
 * Módulo de utilitários e compatibilidade retroativa.
 * Delega configurações seguras e previne o vazamento de segredos no código.
 */

const config = require('./config/config');
const { hashPassword } = require('./services/security.service');

const globalCache = {};
let totalRevenue = 0;

function logAndCache(key, data) {
  globalCache[key] = data;
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
  totalRevenue
};
