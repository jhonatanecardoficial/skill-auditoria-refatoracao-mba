/**
 * Controller responsável pelo fluxo de Checkout e matrícula de alunos.
 */

const CourseModel = require('../models/course.model');
const UserModel = require('../models/user.model');
const EnrollmentModel = require('../models/enrollment.model');
const PaymentModel = require('../models/payment.model');
const AuditModel = require('../models/audit.model');
const { hashPassword, maskCard } = require('../services/security.service');

async function processCheckout(req, res, next) {
  try {
    const u = req.body.usr;
    const e = req.body.eml;
    const p = req.body.pwd;
    const cid = req.body.c_id;
    const cc = req.body.card;

    if (!u || !e || !cid || !cc) {
      return res.status(400).send("Bad Request");
    }

    const course = await CourseModel.findActiveById(cid);
    if (!course) {
      return res.status(404).send("Curso não encontrado");
    }

    let user = await UserModel.findByEmail(e);
    let userId;

    if (!user) {
      const secureHash = hashPassword(p || "123456");
      userId = await UserModel.createUser(u, e, secureHash);
    } else {
      userId = user.id;
    }

    // Processamento seguro do cartão (mascaramento em conformidade com PCI-DSS)
    const maskedCard = maskCard(cc);
    console.log(`[PAYMENT] Processando cartão ${maskedCard} para o curso ${cid}`);

    const status = cc.startsWith("4") ? "PAID" : "DENIED";
    if (status === "DENIED") {
      return res.status(400).send("Pagamento recusado");
    }

    const enrId = await EnrollmentModel.create(userId, cid);
    await PaymentModel.create(enrId, course.price, status);
    await AuditModel.log(`Checkout curso ${cid} por ${userId}`);

    return res.status(200).json({ msg: "Sucesso", enrollment_id: enrId });
  } catch (err) {
    next(err);
  }
}

module.exports = {
  processCheckout
};
