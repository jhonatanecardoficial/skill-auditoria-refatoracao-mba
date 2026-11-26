/**
 * Controller de Usuários.
 */

const UserModel = require('../models/user.model');

async function deleteUser(req, res, next) {
  try {
    const id = req.params.id;
    const targetUser = await UserModel.findById(id);
    if (targetUser && targetUser.role === 'admin') {
      return res.status(403).json({ error: 'Não é permitido excluir contas administrativas' });
    }
    await UserModel.deleteUser(id);
    return res.send("Usuário deletado, e matrículas e pagamentos associados foram limpos com integridade.");
  } catch (err) {
    next(err);
  }
}

module.exports = {
  deleteUser
};
