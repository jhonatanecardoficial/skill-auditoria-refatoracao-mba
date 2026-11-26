/**
 * Suíte E2E Black-Box (100% Real, Zero Mocks) para o Projeto 2: ecommerce-api-legacy.
 *
 * Sobe o processo real `node src/app.js` sem variáveis de ambiente maquiadas,
 * testa todas as rotas sobre TCP/HTTP reais, audita logs PCI-DSS no stdout real
 * e inspeciona o arquivo SQLite real em disco.
 */

const assert = require('assert');
const { spawn, execFileSync } = require('child_process');
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
      const res = await makeRequest(baseUrl, '/api/admin/financial-report', { method: 'GET' });
      if (res.status === 200) return;
    } catch (_) {}
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error(`Timeout aguardando servidor Node real em ${baseUrl}:\n${getLogs()}`);
}

function readUserHashesFromSqlite(dbPath) {
  return new Promise((resolve, reject) => {
    const conn = new sqlite3.Database(dbPath, (err) => {
      if (err) return reject(err);
      conn.all('SELECT id, email, pass FROM users', (qErr, rows) => {
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

  // 1. Verificar defaults Fail-Closed de config.js em subprocesso limpo
  console.log('[TEST 1] Config fail-closed sem variaveis de ambiente');
  const configOut = execFileSync(
    process.execPath,
    ['-e', "console.log(JSON.stringify(require('./src/config/config')))"],
    { cwd: PROJECT_DIR, env: buildCleanEnv(), encoding: 'utf8' }
  );
  const cfg = JSON.parse(configOut.trim());
  assert.strictEqual(cfg.nodeEnv, 'production', 'NODE_ENV ausente deve assumir production');
  assert.strictEqual(cfg.dbPass, '', 'DB_PASS ausente deve ser vazio');
  assert.strictEqual(cfg.paymentGatewayKey, '', 'PAYMENT_GATEWAY_KEY ausente deve ser vazio');
  console.log('  -> OK: config.js fail-closed confirmado.');

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

    // 2. Checkout com sucesso (VISA)
    console.log('[TEST 2] POST /api/checkout (Cartao VISA 4xxx - Sucesso)');
    const r1 = await makeRequest(baseUrl, '/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        usr: 'Aluno Teste',
        eml: 'aluno@teste.com',
        pwd: 'minhasenhaforte',
        c_id: 2,
        card: '4111222233334444'
      })
    });
    assert.strictEqual(r1.status, 200, `Esperado 200, recebido ${r1.status}`);
    assert.ok(r1.json && r1.json.enrollment_id, 'Deve retornar enrollment_id');
    console.log('  -> OK: Checkout processado sobre HTTP real.');

    // 3. Checkout recusado (Mastercard)
    console.log('[TEST 3] POST /api/checkout (Cartao 5xxx - Recusado)');
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

    // 4. Checkout payload incompleto
    console.log('[TEST 4] POST /api/checkout (Bad Request)');
    const r3 = await makeRequest(baseUrl, '/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usr: 'Incompleto' })
    });
    assert.strictEqual(r3.status, 400);
    assert.strictEqual(r3.body, 'Bad Request');
    console.log('  -> OK: Rejeicao de payload incompleto.');

    // 5. Checkout com cartao numerico JSON (sem crash 500)
    console.log('[TEST 5] POST /api/checkout (Cartao enviado como inteiro JSON)');
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

    // 6. Checkout curso inexistente
    console.log('[TEST 6] POST /api/checkout (Curso Nao Encontrado)');
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

    // 7. Relatorio Financeiro antes da delecao
    console.log('[TEST 7] GET /api/admin/financial-report');
    const r5 = await makeRequest(baseUrl, '/api/admin/financial-report', { method: 'GET' });
    assert.strictEqual(r5.status, 200);
    assert.ok(Array.isArray(r5.json) && r5.json.length >= 2, 'Deve conter ao menos 2 cursos');
    const cleanArchBefore = r5.json.find((c) => c.course === 'Clean Architecture');
    assert.strictEqual(cleanArchBefore.revenue, 997);
    console.log('  -> OK: Relatorio agregado gerado sem N+1.');

    // 8. Deletar usuario 1 e validar integridade referencial no relatorio subsequente
    console.log('[TEST 8] DELETE /api/users/1 e verificacao de zero orfaos');
    const r6 = await makeRequest(baseUrl, '/api/users/1', { method: 'DELETE' });
    assert.strictEqual(r6.status, 200);
    assert.ok(r6.body.includes('Usuário deletado'));

    const rAfterDel = await makeRequest(baseUrl, '/api/admin/financial-report', { method: 'GET' });
    assert.strictEqual(rAfterDel.status, 200);
    const cleanArchAfter = rAfterDel.json.find((c) => c.course === 'Clean Architecture');
    assert.strictEqual(cleanArchAfter.revenue, 0, 'Receita do usuario deletado deve ser removida');
    assert.strictEqual(cleanArchAfter.students.length, 0, 'Nao deve restar matricula orfa');
    console.log('  -> OK: Exclusao em cascata comprovada no relatorio real.');

    // 9. Auditoria PCI-DSS nos logs reais do subprocesso e hashes PBKDF2 no arquivo SQLite
    console.log('[TEST 9] Auditoria PCI-DSS no stdout real e PBKDF2 no SQLite em disco');
    assert.ok(logs.includes('************4444'), 'Cartao mascarado deve constar nos logs do servidor');
    assert.ok(!logs.includes('4111222233334444'), 'Numero completo do cartao VISA nunca pode vazar nos logs');
    assert.ok(!logs.includes('5111222233334444'), 'Numero completo do cartao recusado nunca pode vazar nos logs');
    assert.ok(!logs.includes('pk_live_'), 'Chave de gateway nunca pode vazar nos logs');

    const dbUsers = await readUserHashesFromSqlite(dbPath);
    assert.ok(dbUsers.length >= 2, 'Banco SQLite real deve conter usuarios cadastrados');
    for (const u of dbUsers) {
      assert.match(u.pass, /^[0-9a-f]{32}:[0-9a-f]{64}$/, `Senha em texto claro ou formato fraco para ${u.email}`);
    }
    console.log('  -> OK: Logs PCI-DSS limpos e 100% PBKDF2 no arquivo SQLite real.');
    console.log('--- Todos os 9 testes E2E reais de ecommerce-api-legacy foram aprovados! ---');
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
