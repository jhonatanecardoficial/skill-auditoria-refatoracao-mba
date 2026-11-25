/**
 * Model de persistência e agregação para Relatórios Administrativos.
 * Encapsula consultas de faturamento e matrículas, eliminando SQL direto em controllers.
 */

const { dbAll } = require('../database/db');

class ReportModel {
  /**
   * Obtém dados consolidados de cursos, matrículas, alunos e pagamentos.
   * Utiliza LEFT JOINs para evitar o anti-pattern N+1 Query.
   * @returns {Promise<Array>} Lista de registros agregados.
   */
  static async getFinancialReportData() {
    const query = `
      SELECT
        c.id AS course_id,
        c.title AS course_title,
        e.id AS enrollment_id,
        u.name AS student_name,
        p.amount AS paid_amount,
        p.status AS payment_status
      FROM courses c
      LEFT JOIN enrollments e ON c.id = e.course_id
      LEFT JOIN users u ON e.user_id = u.id
      LEFT JOIN payments p ON e.id = p.enrollment_id
      ORDER BY c.id ASC
    `;
    return await dbAll(query);
  }
}

module.exports = ReportModel;
