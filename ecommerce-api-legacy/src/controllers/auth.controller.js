/**
 * Controller de Autenticação (Login e emissão de Bearer tokens HMAC-SHA256).
 */

const UserModel = require('../models/user.model');
const { verifyPassword, generateAuthToken } = require('../services/security.service');

async function login(req, res, next) {
  try {
    const body = req.body || {};
    const email = (body.email || body.eml || '').trim();
    const password = body.password || body.pwd || '';

    if (!email || !password) {
      return res.status(400).json({ error: 'Email e senha são obrigatórios' });
    }

    const user = await UserModel.findByEmail(email);
    if (!user || !verifyPassword(password, user.pass)) {
      return res.status(401).json({ error: 'Credenciais inválidas' });
    }

    const safeUser = {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role || 'student'
    };
    const token = generateAuthToken(safeUser);
    return res.status(200).json({
      message: 'Login realizado com sucesso',
      token,
      user: safeUser
    });
  } catch (err) {
    return next(err);
  }
}

module.exports = {
  login
};
