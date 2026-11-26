/**
 * Serviço de segurança, criptografia e tokens autenticados (HMAC-SHA256).
 * Fornece hashing seguro com salt, assinatura/verificação de tokens e mascaramento PCI-DSS.
 */

const crypto = require('crypto');
const config = require('../config/config');

const DEFAULT_TOKEN_TTL_MS = 24 * 60 * 60 * 1000;

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
 * Valida se uma senha informada corresponde ao hash seguro armazenado em tempo constante.
 * @param {string} password - Senha informada.
 * @param {string} storedHash - Hash persistido.
 * @returns {boolean} True se a senha for válida.
 */
function verifyPassword(password, storedHash) {
  if (!storedHash || !password) return false;
  if (storedHash.includes(':')) {
    const [salt, originalHash] = storedHash.split(':');
    const hash = crypto.pbkdf2Sync(password, salt, 10000, 32, 'sha256').toString('hex');
    const bufHash = Buffer.from(hash, 'hex');
    const bufOriginal = Buffer.from(originalHash || '', 'hex');
    if (bufHash.length !== bufOriginal.length) return false;
    return crypto.timingSafeEqual(bufHash, bufOriginal);
  }
  return false;
}

/**
 * Emite token Bearer assinado com HMAC-SHA256 e expiração embutida.
 * @param {Object} user - Registro do usuário autenticado.
 * @param {number} maxAgeMs - Validade máxima em milissegundos.
 * @returns {string} Token assinado no formato base64url.hmacHex.
 */
function generateAuthToken(user, maxAgeMs = DEFAULT_TOKEN_TTL_MS) {
  const payload = {
    id: user.id,
    email: user.email,
    role: user.role || 'student',
    exp: Date.now() + maxAgeMs
  };
  const encodedPayload = Buffer.from(JSON.stringify(payload), 'utf8').toString('base64url');
  const signature = crypto
    .createHmac('sha256', config.secretKey)
    .update(encodedPayload)
    .digest('hex');
  return `${encodedPayload}.${signature}`;
}

/**
 * Verifica assinatura HMAC-SHA256 em tempo constante e validade temporal do token.
 * @param {string} token - Token Bearer recebido.
 * @returns {Object|null} Payload decodificado ou null se inválido/expirado.
 */
function verifyAuthToken(token) {
  if (!token || typeof token !== 'string' || !token.includes('.')) return null;
  const parts = token.split('.');
  if (parts.length !== 2) return null;
  const [encodedPayload, signatureHex] = parts;
  if (!encodedPayload || !signatureHex || !/^[0-9a-f]+$/i.test(signatureHex)) return null;

  const expectedSigHex = crypto
    .createHmac('sha256', config.secretKey)
    .update(encodedPayload)
    .digest('hex');

  const bufProvided = Buffer.from(signatureHex, 'hex');
  const bufExpected = Buffer.from(expectedSigHex, 'hex');
  if (bufProvided.length !== bufExpected.length) return null;
  if (!crypto.timingSafeEqual(bufProvided, bufExpected)) return null;

  try {
    const payload = JSON.parse(Buffer.from(encodedPayload, 'base64url').toString('utf8'));
    if (!payload || typeof payload.exp !== 'number' || payload.exp <= Date.now()) {
      return null;
    }
    return payload;
  } catch (_) {
    return null;
  }
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
  generateAuthToken,
  verifyAuthToken,
  maskCard
};
