/**
 * Middleware centralizado de tratamento de erros no Express.
 */

function errorHandler(err, req, res, next) {
  console.error('[SERVER ERROR]', err);
  const status = err.status || 500;
  const message = err.message || 'Erro interno no servidor';
  res.status(status).json({ error: message, status });
}

module.exports = errorHandler;
