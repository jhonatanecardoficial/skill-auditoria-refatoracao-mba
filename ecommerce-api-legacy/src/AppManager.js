/**
 * AppManager - Fachada de compatibilidade arquitetural.
 * Conecta a inicialização do banco e o registro de rotas modularizadas no Express.
 */

const { db, initDb } = require('./database/db');
const apiRoutes = require('./routes');

class AppManager {
  constructor() {
    this.db = db;
  }

  initDb() {
    initDb();
  }

  setupRoutes(app) {
    app.use('/api', apiRoutes);
  }
}

module.exports = AppManager;
