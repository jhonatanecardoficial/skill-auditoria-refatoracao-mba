/**
 * Controller responsável pelos Relatórios Administrativos.
 * Utiliza o ReportModel para busca de dados e formata o resultado para apresentação.
 */

const ReportModel = require('../models/report.model');

async function getFinancialReport(req, res, next) {
  try {
    const rows = await ReportModel.getFinancialReportData();

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
    return res.status(200).json(report);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  getFinancialReport
};
