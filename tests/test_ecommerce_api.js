/**
 * Suíte E2E Black-Box (100% Real, Zero Mocks) para o Projeto 2: ecommerce-api-legacy.
 *
 * Sobe o processo real `node src/app.js` sem variáveis de ambiente maquiadas,
 * testa todas as rotas sobre TCP/HTTP reais (incluindo proteção Bearer HMAC em
 * /api/admin/financial-report), audita logs PCI-DSS no stdout real
 * e inspeciona o arquivo SQLite real em disco.
 */

const assert = require('assert');
const { spawn, execFileSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const net = require('net');
const os = require('os');
const path = require('path');

const PROJECT_DIR = path.resolve(__dirname, '..', 'ecommerce-api-legacy');
const sqlite3 = require(path.join(PROJECT_DIR, 'node_modules', 'sqlite3'));

const ENV_KEYS_TO_STRIP = [
  'NODE_ENV',
  'ENVIRONMENT',
  'DB_PATH',
  'DB_USER',
  'DB_PASS',
  'PAYMENT_GATEWAY_KEY',
  'SMTP_USER',
  'SECRET_KEY',
  'PORT'
];

function buildCleanEnv(overrides = {}) {
  const env = { ...process.env };
  for (const key of ENV_KEYS_TO_STRIP) {
    delete env[key];
  }
  return { ...env, ...overrides };
}

function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

function makeRequest(baseUrl, reqPath, options = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(baseUrl + reqPath);
    const req = http.request(url, options, (res) => {
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(body); } catch (_) {}
        resolve({ status: res.statusCode, body, json });
      });
    });
    req.on('error', reject);
    if (options.body) req.write(options.body);
    req.end();
  });
}

async function waitForReady(baseUrl, child, getLogs) {
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`Servidor Node encerrou prematuramente (code=${child.exitCode}):\n${getLogs()}`);
    }
    try {
      // Sem token, a rota administrativa protegida deve responder 401 assim que o boot concluir
      const res = await makeRequest(baseUrl, '/api/admin/financial-report', { method: 'GET' });
      if (res.status === 401) return;
    } catch (_) {}
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error(`Timeout aguardando servidor Node real em ${baseUrl}:\n${getLogs()}`);
}

function readUsersFromSqlite(dbPath) {
  return new Promise((resolve, reject) => {
    const conn = new sqlite3.Database(dbPath, (err) => {
      if (err) return reject(err);
      conn.all('SELECT id, email, pass, role FROM users', (qErr, rows) => {
        conn.close(() => {
          if (qErr) return reject(qErr);
          resolve(rows);
        });
      });
    });
  });
}

async function runTests() {
  console.log('--- Iniciando Testes E2E Reais (Zero Mocks) de ecommerce-api-legacy ---');

  // 1. Verificar defaults Fail-Closed e secretKey efêmera em subprocessos limpos
  console.log('[TEST 1] Config fail-closed e secretKey efemera sem variaveis de ambiente');
  const script = "console.log(JSON.stringify(require('./src/config/config')))";
  const cfg1 = JSON.parse(execFileSync(process.execPath, ['-e', script], { cwd: PROJECT_DIR, env: buildCleanEnv(), encoding: 'utf8' }).trim());
  const cfg2 = JSON.parse(execFileSync(process.execPath, ['-e', script], { cwd: PROJECT_DIR, env: buildCleanEnv(), encoding: 'utf8' }).trim());
  assert.strictEqual(cfg1.nodeEnv, 'production', 'NODE_ENV ausente deve assumir production');
  assert.strictEqual(cfg1.dbPass, '', 'DB_PASS ausente deve ser vazio');
  assert.strictEqual(cfg1.paymentGatewayKey, '', 'PAYMENT_GATEWAY_KEY ausente deve ser vazio');
  assert.strictEqual(cfg1.secretKey.length, 64, 'secretKey efemera deve ter 256 bits em hex');
  assert.notStrictEqual(cfg1.secretKey, cfg2.secretKey, 'secretKey ausente deve ser unica por processo');
  console.log('  -> OK: config.js fail-closed + CSPRNG confirmado.');

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'e2e_ecommerce_'));
  const dbPath = path.join(tmpDir, 'e2e_lms.db');
  const port = await getFreePort();
  const baseUrl = `http://127.0.0.1:${port}`;

  let logs = '';
  const serverProc = spawn(process.execPath, ['src/app.js'], {
    cwd: PROJECT_DIR,
    env: buildCleanEnv({ PORT: String(port), DB_PATH: dbPath }),
    stdio: ['ignore', 'pipe', 'pipe']
  });
  serverProc.stdout.on('data', (chunk) => { logs += chunk.toString(); });
  serverProc.stderr.on('data', (chunk) => { logs += chunk.toString(); });

  try {
    await waitForReady(baseUrl, serverProc, () => logs);

    // 2. Red-Team: /api/admin/financial-report sem token deve retornar 401
    console.log('[TEST 2] Red-Team GET /api/admin/financial-report sem token -> 401');
    const rNoAuth = await makeRequest(baseUrl, '/api/admin/financial-report', { method: 'GET' });
    assert.strictEqual(rNoAuth.status, 401, `Esperado 401, recebido ${rNoAuth.status}`);
    console.log('  -> OK: Acesso anonimo ao relatorio financeiro bloqueado com 401.');

    // 3. Red-Team: token forjado com chave estática -> 401
    console.log('[TEST 3] Red-Team GET /api/admin/financial-report com token forjado -> 401');
    const forgedPayload = Buffer.from(JSON.stringify({ id: 2, email: 'admin@fullcycle.com.br', role: 'admin', exp: Date.now() + 60000 })).toString('base64url');
    const forgedSig = crypto.createHmac('sha256', 'forged-static-secret').update(forgedPayload).digest('hex');
    const rForged = await makeRequest(baseUrl, '/api/admin/financial-report', {
      method: 'GET',
      headers: { Authorization: `Bearer ${forgedPayload}.${forgedSig}` }
    });
    assert.strictEqual(rForged.status, 401, `Esperado 401 para token forjado, recebido ${rForged.status}`);
    console.log('  -> OK: Token forjado rejeitado com 401.');

    // 4. Checkout com sucesso (VISA) tentando injetar role: 'admin' (Mass Assignment)
    console.log('[TEST 4] POST /api/checkout (VISA 4xxx + tentativa role=admin no body)');
    const r1 = await makeRequest(baseUrl, '/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        usr: 'Aluno Teste',
        eml: 'aluno@teste.com',
        pwd: 'minhasenhaforte',
        role: 'admin',
        c_id: 2,
        card: '4111222233334444'
      })
    });
    assert.strictEqual(r1.status, 200, `Esperado 200, recebido ${r1.status}`);
    assert.ok(r1.json && r1.json.enrollment_id, 'Deve retornar enrollment_id');
    console.log('  -> OK: Checkout processado sobre HTTP real.');

    // 5. Red-Team: aluno loga via POST /api/login e tenta acessar relatorio financeiro -> 403
    console.log('[TEST 5] Red-Team Anti-Mass Assignment + RBAC (aluno tentando /api/admin/financial-report -> 403)');
    const rLoginStudent = await makeRequest(baseUrl, '/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'aluno@teste.com', password: 'minhasenhaforte' })
    });
    assert.strictEqual(rLoginStudent.status, 200);
    assert.strictEqual(rLoginStudent.json.user.role, 'student', 'Checkout publico nunca pode criar admin');
    assert.strictEqual(rLoginStudent.json.user.pass, undefined, 'Login nao deve expor hash de senha');

    const rStudentAdminReport = await makeRequest(baseUrl, '/api/admin/financial-report', {
      method: 'GET',
      headers: { Authorization: `Bearer ${rLoginStudent.json.token}` }
    });
    assert.strictEqual(rStudentAdminReport.status, 403, `Aluno deveria receber 403, recebeu ${rStudentAdminReport.status}`);
    console.log('  -> OK: Auto-elevacao bloqueada e aluno barrado com 403 no /api/admin/financial-report.');

    // 6. Checkout recusado (Mastercard)
    console.log('[TEST 6] POST /api/checkout (Cartao 5xxx - Recusado)');
    const r2 = await makeRequest(baseUrl, '/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        usr: 'Aluno 2',
        eml: 'aluno2@teste.com',
        pwd: '123',
        c_id: 1,
        card: '5111222233334444'
      })
    });
    assert.strictEqual(r2.status, 400);
    assert.strictEqual(r2.body, 'Pagamento recusado');
    console.log('  -> OK: Pagamento recusado conforme regra.');

    // 7. Checkout payload incompleto
    console.log('[TEST 7] POST /api/checkout (Bad Request)');
    const r3 = await makeRequest(baseUrl, '/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usr: 'Incompleto' })
    });
    assert.strictEqual(r3.status, 400);
    assert.strictEqual(r3.body, 'Bad Request');
    console.log('  -> OK: Rejeicao de payload incompleto.');

    // 8. Checkout com cartao numerico JSON (sem crash 500)
    console.log('[TEST 8] POST /api/checkout (Cartao enviado como inteiro JSON)');
    const rNum = await makeRequest(baseUrl, '/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        usr: 'Aluno Numerico',
        eml: 'alunonum@teste.com',
        pwd: 'segredo123',
        c_id: 2,
        card: 4111222233334444
      })
    });
    assert.strictEqual(rNum.status, 200, `Esperado 200 para cartao numerico, recebido ${rNum.status}`);
    console.log('  -> OK: Cartao numerico tratado sem erro 500.');

    // 9. Checkout curso inexistente
    console.log('[TEST 9] POST /api/checkout (Curso Nao Encontrado)');
    const r4 = await makeRequest(baseUrl, '/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        usr: 'Aluno 3',
        eml: 'aluno3@teste.com',
        pwd: '123',
        c_id: 9999,
        card: '4111222233334444'
      })
    });
    assert.strictEqual(r4.status, 404);
    assert.strictEqual(r4.body, 'Curso não encontrado');
    console.log('  -> OK: 404 retornado para curso invalido.');

    // 10. Login admin real e consulta autorizada a GET /api/admin/financial-report
    console.log('[TEST 10] POST /api/login admin + GET /api/admin/financial-report -> 200');
    const rLoginAdmin = await makeRequest(baseUrl, '/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'admin@fullcycle.com.br', password: 'admin123' })
    });
    assert.strictEqual(rLoginAdmin.status, 200);
    assert.strictEqual(rLoginAdmin.json.user.role, 'admin');
    const adminToken = rLoginAdmin.json.token;

    const r5 = await makeRequest(baseUrl, '/api/admin/financial-report', {
      method: 'GET',
      headers: { Authorization: `Bearer ${adminToken}` }
    });
    assert.strictEqual(r5.status, 200);
    assert.ok(Array.isArray(r5.json) && r5.json.length >= 2, 'Relatorio deve conter ao menos 2 cursos');
    const cleanArchBefore = r5.json.find((c) => c.course === 'Clean Architecture');
    assert.strictEqual(cleanArchBefore.revenue, 997);
    console.log('  -> OK: Relatorio financeiro protegido respondendo 200 para admin autenticado.');

    // 11. Bloqueio de exclusao do admin (id=2 -> 403) + exclusao do aluno Leonan (id=1 -> 200) sem orfaos
    console.log('[TEST 11] Protecao contra DELETE /api/users/2 (admin) + DELETE /api/users/1 sem orfaos');
    const rDelAdmin = await makeRequest(baseUrl, '/api/users/2', { method: 'DELETE' });
    assert.strictEqual(rDelAdmin.status, 403, `Conta admin nao pode ser excluida, recebeu ${rDelAdmin.status}`);

    const r6 = await makeRequest(baseUrl, '/api/users/1', { method: 'DELETE' });
    assert.strictEqual(r6.status, 200);
    assert.ok(r6.body.includes('Usuário deletado'));

    const rAfterDel = await makeRequest(baseUrl, '/api/admin/financial-report', {
      method: 'GET',
      headers: { Authorization: `Bearer ${adminToken}` }
    });
    assert.strictEqual(rAfterDel.status, 200);
    const cleanArchAfter = rAfterDel.json.find((c) => c.course === 'Clean Architecture');
    assert.strictEqual(cleanArchAfter.revenue, 0, 'Receita do usuario deletado deve ser removida');
    assert.strictEqual(cleanArchAfter.students.length, 0, 'Nao deve restar matricula orfa');
    console.log('  -> OK: Exclusao em cascata comprovada e conta admin preservada.');

    // 12. Auditoria PCI-DSS nos logs reais e PBKDF2/roles no SQLite em disco
    console.log('[TEST 12] Auditoria PCI-DSS no stdout real e PBKDF2/roles no SQLite em disco');
    assert.ok(logs.includes('************4444'), 'Cartao mascarado deve constar nos logs do servidor');
    assert.ok(!logs.includes('4111222233334444'), 'Numero completo do cartao VISA nunca pode vazar nos logs');
    assert.ok(!logs.includes('5111222233334444'), 'Numero completo do cartao recusado nunca pode vazar nos logs');
    assert.ok(!logs.includes('pk_live_'), 'Chave de gateway nunca pode vazar nos logs');

    const dbUsers = await readUsersFromSqlite(dbPath);
    assert.ok(dbUsers.length >= 3, 'Banco SQLite real deve conter usuarios cadastrados');
    for (const u of dbUsers) {
      assert.match(u.pass, /^[0-9a-f]{32}:[0-9a-f]{64}$/, `Senha em texto claro ou formato fraco para ${u.email}`);
      if (u.email === 'admin@fullcycle.com.br') {
        assert.strictEqual(u.role, 'admin');
      } else {
        assert.strictEqual(u.role, 'student', `Usuario publico ${u.email} recebeu papel inesperado: ${u.role}`);
      }
    }
    console.log('  -> OK: Logs PCI-DSS limpos, 100% PBKDF2 e menor privilegio no SQLite real.');
    console.log('--- Todos os 12 testes E2E reais de ecommerce-api-legacy foram aprovados! ---');
  } finally {
    if (serverProc.exitCode === null) {
      serverProc.kill();
      await new Promise((r) => serverProc.once('exit', r));
    }
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

runTests().catch((err) => {
  console.error('FALHA NOS TESTES:', err);
  process.exit(1);
});
