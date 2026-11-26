/**
 * Middleware de autenticação Bearer (HMAC-SHA256) e autorização administrativa.
 */

const UserModel = require('../models/user.model');
const { verifyAuthToken } = require('../services/security.service');

/**
 * Protege rotas administrativas exigindo Bearer token assinado e revalidando role === 'admin' no SQLite.
 */
async function requireAdmin(req, res, next) {
  try {
    const authHeader = req.headers.authorization || '';
    if (!authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Token de autenticação não fornecido' });
    }

    const token = authHeader.slice(7).trim();
    const userData = verifyAuthToken(token);
    if (!userData) {
      return res.status(401).json({ error: 'Token inválido ou expirado' });
    }

    const dbUser = userData.id ? await UserModel.findById(userData.id) : null;
    if (!dbUser || userData.role !== 'admin' || dbUser.role !== 'admin') {
      return res.status(403).json({ error: 'Acesso restrito a administradores' });
    }

    req.user = dbUser;
    return next();
  } catch (err) {
    return next(err);
  }
}

module.exports = {
  requireAdmin
};
