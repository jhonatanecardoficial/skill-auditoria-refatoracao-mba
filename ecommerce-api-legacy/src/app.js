/**
 * Servidor Express e ponto de entrada da API LMS E-commerce.
 */

const express = require('express');
const AppManager = require('./AppManager');
const config = require('./config/config');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

const manager = new AppManager();
manager.initDb();
manager.setupRoutes(app);

app.use(errorHandler);

if (require.main === module) {
  app.listen(config.port, () => {
    console.log(`LMS API refatorada rodando com sucesso na porta ${config.port}...`);
  });
}

module.exports = app;
