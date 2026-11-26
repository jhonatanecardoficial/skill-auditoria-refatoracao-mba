/**
 * Controller responsável pelo fluxo de Checkout e matrícula de alunos.
 * Valida os dados da requisição, orquestra models e assegura conformidade PCI-DSS.
 */

const crypto = require('crypto');
const CourseModel = require('../models/course.model');
const UserModel = require('../models/user.model');
const EnrollmentModel = require('../models/enrollment.model');
const PaymentModel = require('../models/payment.model');
const AuditModel = require('../models/audit.model');
const { hashPassword, maskCard } = require('../services/security.service');
const { logAndCache } = require('../utils');

const VISA_CARD_PREFIX = '4';

async function processCheckout(req, res, next) {
  try {
    const body = req.body || {};
    const userName = body.usr;
    const email = body.eml;
    const rawPassword = body.pwd;
    const courseId = body.c_id;
    const cardNumber = body.card !== undefined && body.card !== null ? String(body.card).trim() : '';

    // Validação de presença dos campos obrigatórios do contrato da API
    if (!userName || !email || !courseId || !cardNumber) {
      return res.status(400).send("Bad Request");
    }

    const course = await CourseModel.findActiveById(courseId);
    if (!course) {
      return res.status(404).send("Curso não encontrado");
    }

    let user = await UserModel.findByEmail(email);
    let userId;

    if (!user) {
      const passwordToHash = rawPassword || crypto.randomBytes(16).toString('hex');
      const secureHash = hashPassword(passwordToHash);
      // Regra Anti-Mass Assignment: cadastro via checkout público força papel 'student'
      userId = await UserModel.createUser(userName, email, secureHash, 'student');
    } else {
      userId = user.id;
    }

    // Processamento seguro do cartão (mascaramento em conformidade com PCI-DSS)
    const maskedCard = maskCard(cardNumber);
    console.log(`[PAYMENT] Processando cartão ${maskedCard} para o curso ${courseId}`);

    const status = cardNumber.startsWith(VISA_CARD_PREFIX) ? "PAID" : "DENIED";
    if (status === "DENIED") {
      return res.status(400).send("Pagamento recusado");
    }

    const enrollmentId = await EnrollmentModel.create(userId, courseId);
    await PaymentModel.create(enrollmentId, course.price, status);
    await AuditModel.log(`Checkout curso ${courseId} por ${userId}`);
    logAndCache(`last_checkout_${userId}`, course.title);

    return res.status(200).json({ msg: "Sucesso", enrollment_id: enrollmentId });
  } catch (err) {
    next(err);
  }
}

module.exports = {
  processCheckout
};
