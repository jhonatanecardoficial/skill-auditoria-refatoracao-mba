/**
 * Rotas de Checkout.
 */

const express = require('express');
const { processCheckout } = require('../controllers/checkout.controller');

const router = express.Router();

router.post('/checkout', processCheckout);

module.exports = router;
