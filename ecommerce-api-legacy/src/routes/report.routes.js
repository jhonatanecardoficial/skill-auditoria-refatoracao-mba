/**
 * Rotas Administrativas de Relatório.
 */

const express = require('express');
const { getFinancialReport } = require('../controllers/report.controller');

const router = express.Router();

router.get('/admin/financial-report', getFinancialReport);

module.exports = router;
