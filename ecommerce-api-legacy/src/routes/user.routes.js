/**
 * Rotas de Usuário.
 */

const express = require('express');
const { deleteUser } = require('../controllers/user.controller');

const router = express.Router();

router.delete('/users/:id', deleteUser);

module.exports = router;
