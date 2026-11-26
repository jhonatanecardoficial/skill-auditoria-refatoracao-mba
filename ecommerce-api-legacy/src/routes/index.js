/**
 * Centralizador de rotas da aplicação.
 */

const express = require('express');
const authRoutes = require('./auth.routes');
const checkoutRoutes = require('./checkout.routes');
const reportRoutes = require('./report.routes');
const userRoutes = require('./user.routes');

const apiRouter = express.Router();

apiRouter.use(authRoutes);
apiRouter.use(checkoutRoutes);
apiRouter.use(reportRoutes);
apiRouter.use(userRoutes);

module.exports = apiRouter;
