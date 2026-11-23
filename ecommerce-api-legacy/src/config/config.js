/**
 * Configurações da aplicação LMS E-commerce.
 * Centraliza variáveis de ambiente e valores padrão seguros.
 */

const config = {
  port: parseInt(process.env.PORT || "3000", 10),
  dbUser: process.env.DB_USER || "admin_master",
  dbPass: process.env.DB_PASS || "dev_secure_password_fallback",
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "pk_test_sample_key",
  smtpUser: process.env.SMTP_USER || "no-reply@fullcycle.com.br",
  nodeEnv: process.env.NODE_ENV || "development"
};

module.exports = config;
