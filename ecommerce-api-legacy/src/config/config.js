/**
 * Configurações da aplicação LMS E-commerce.
 * Centraliza variáveis de ambiente com comportamento fail-closed e sem segredos estáticos.
 */

const config = {
  port: parseInt(process.env.PORT || "3000", 10),
  dbPath: process.env.DB_PATH || ":memory:",
  dbUser: process.env.DB_USER || "",
  dbPass: process.env.DB_PASS || "",
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "",
  smtpUser: process.env.SMTP_USER || "",
  nodeEnv: (process.env.NODE_ENV || "production").trim().toLowerCase()
};

module.exports = config;
