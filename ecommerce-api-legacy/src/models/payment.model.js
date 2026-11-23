/**
 * Model de persistência para Pagamentos.
 */

const { dbGet, dbRun } = require('../database/db');

class PaymentModel {
  static async create(enrollmentId, amount, status) {
    const result = await dbRun(
      "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
      [enrollmentId, amount, status]
    );
    return result.lastID;
  }

  static async findByEnrollmentId(enrollmentId) {
    return await dbGet(
      "SELECT amount, status FROM payments WHERE enrollment_id = ?",
      [enrollmentId]
    );
  }
}

module.exports = PaymentModel;
