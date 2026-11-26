/**
 * Rotas Administrativas de Relatório.
 */

const express = require('express');
const { getFinancialReport } = require('../controllers/report.controller');
const { requireAdmin } = require('../middlewares/authMiddleware');

const router = express.Router();

router.get('/admin/financial-report', requireAdmin, getFinancialReport);

module.exports = router;
