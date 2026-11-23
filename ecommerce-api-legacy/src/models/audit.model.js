/**
 * Model de persistência para Logs de Auditoria.
 */

const { dbRun } = require('../database/db');

class AuditModel {
  static async log(action) {
    const result = await dbRun(
      "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
      [action]
    );
    return result.lastID;
  }
}

module.exports = AuditModel;
