/**
 * Módulo de conexão e gerenciamento do banco de dados SQLite.
 * Fornece métodos assíncronos baseados em Promises para evitar Callback Hell.
 */

const sqlite3 = require('sqlite3').verbose();
const { hashPassword } = require('../services/security.service');

// Instância compartilhada do banco SQLite em memória
const db = new sqlite3.Database(':memory:');

/**
 * Executa uma consulta que retorna uma única linha com Promise.
 * @param {string} sql - Comando SQL parametrizado.
 * @param {Array} params - Parâmetros da query.
 * @returns {Promise<Object|null>} Linha encontrada ou null.
 */
function dbGet(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) return reject(err);
      resolve(row || null);
    });
  });
}

/**
 * Executa uma consulta que retorna múltiplas linhas com Promise.
 * @param {string} sql - Comando SQL parametrizado.
 * @param {Array} params - Parâmetros da query.
 * @returns {Promise<Array>} Lista de registros.
 */
function dbAll(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) return reject(err);
      resolve(rows || []);
    });
  });
}

/**
 * Executa um comando SQL de mutação (INSERT, UPDATE, DELETE) com Promise.
 * @param {string} sql - Comando SQL parametrizado.
 * @param {Array} params - Parâmetros da query.
 * @returns {Promise<{lastID: number, changes: number}>} Metadados da execução.
 */
function dbRun(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) return reject(err);
      resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
}

/**
 * Inicializa schemas das tabelas e popula dados de seed de forma serializada no SQLite.
 * Assegura que senhas de seed sejam devidamente hasheadas com salt seguro.
 */
function initDb() {
  db.serialize(() => {
    db.run("PRAGMA foreign_keys = ON;");
    db.run("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, pass TEXT)");
    db.run("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price REAL, active INTEGER)");
    db.run("CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, course_id INTEGER, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE)");
    db.run("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_id INTEGER, amount REAL, status TEXT, FOREIGN KEY(enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE)");
    db.run("CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)");

    const seedPasswordHash = hashPassword('123');
    db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', ?)", [seedPasswordHash]);
    db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
    db.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
    db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
  });
}

module.exports = {
  db,
  dbGet,
  dbAll,
  dbRun,
  initDb
};
