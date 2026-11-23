/**
 * Controller responsável pelos Relatórios Administrativos.
 * Elimina o problema N+1 através de agregações relacionais otimizadas.
 */

const { dbAll } = require('../database/db');

async function getFinancialReport(req, res, next) {
  try {
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

    const rows = await dbAll(query);

    const reportMap = new Map();

    for (const row of rows) {
      if (!reportMap.has(row.course_id)) {
        reportMap.set(row.course_id, {
          course: row.course_title,
          revenue: 0,
          students: []
        });
      }

      const courseData = reportMap.get(row.course_id);

      if (row.enrollment_id) {
        const isPaid = row.payment_status === 'PAID';
        const paidAmount = (isPaid && row.paid_amount) ? row.paid_amount : 0;

        if (isPaid) {
          courseData.revenue += paidAmount;
        }

        courseData.students.push({
          student: row.student_name || 'Unknown',
          paid: row.paid_amount || 0
        });
      }
    }

    const report = Array.from(reportMap.values());
    return res.json(report);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  getFinancialReport
};
