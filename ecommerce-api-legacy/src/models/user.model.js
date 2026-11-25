/**
 * Model de persistência para Usuários.
 */

const { dbGet, dbRun } = require('../database/db');

class UserModel {
  static async findByEmail(email) {
    return await dbGet("SELECT * FROM users WHERE email = ?", [email]);
  }

  static async findById(id) {
    return await dbGet("SELECT id, name, email FROM users WHERE id = ?", [id]);
  }

  static async createUser(name, email, passwordHash) {
    const result = await dbRun(
      "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
      [name, email, passwordHash]
    );
    return result.lastID;
  }

  static async deleteUser(id) {
    // Exclui pagamentos e matrículas associadas em lote relacional sem N+1 deletes
    await dbRun(
      "DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)",
      [id]
    );
    await dbRun("DELETE FROM enrollments WHERE user_id = ?", [id]);
    const result = await dbRun("DELETE FROM users WHERE id = ?", [id]);
    return result.changes > 0;
  }
}

module.exports = UserModel;
