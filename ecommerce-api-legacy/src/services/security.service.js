/**
 * Serviço de segurança e criptografia.
 * Fornece hashing seguro com salt e mascaramento de dados sensíveis (PCI-DSS).
 */

const crypto = require('crypto');

/**
 * Gera um hash criptográfico seguro para a senha com salt aleatório.
 * @param {string} password - Senha em texto plano.
 * @returns {string} String codificada contendo salt e hash em formato seguro.
 */
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, salt, 10000, 32, 'sha256').toString('hex');
  return `${salt}:${hash}`;
}

/**
 * Valida se uma senha informada corresponde ao hash seguro ou legado armazenado.
 * @param {string} password - Senha informada.
 * @param {string} storedHash - Hash persistido.
 * @returns {boolean} True se a senha for válida.
 */
function verifyPassword(password, storedHash) {
  if (!storedHash) return false;
  if (storedHash.includes(':')) {
    const [salt, originalHash] = storedHash.split(':');
    const hash = crypto.pbkdf2Sync(password, salt, 10000, 32, 'sha256').toString('hex');
    return hash === originalHash;
  }
  // Suporte a senhas legadas em texto plano de seeds
  return password === storedHash;
}

/**
 * Mascara o número do cartão de crédito, mantendo visíveis apenas os 4 últimos dígitos.
 * @param {string} cardNumber - Número do cartão.
 * @returns {string} Número mascarado (ex: ************4444).
 */
function maskCard(cardNumber) {
  if (!cardNumber || typeof cardNumber !== 'string') return '****';
  return cardNumber.replace(/.(?=.{4})/g, '*');
}

module.exports = {
  hashPassword,
  verifyPassword,
  maskCard
};
