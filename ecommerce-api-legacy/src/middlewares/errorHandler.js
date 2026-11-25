/**
 * Middleware centralizado de tratamento de erros no Express.
 * Padroniza respostas de erro e assegura que stack traces não sejam vazados para o cliente.
 */

function errorHandler(err, req, res, next) {
  console.error('[SERVER ERROR]', err);
  const status = err.status || 500;
  const message = status === 500 ? 'Erro interno no servidor' : (err.message || 'Erro');
  res.status(status).json({ error: message, status });
}

module.exports = errorHandler;
