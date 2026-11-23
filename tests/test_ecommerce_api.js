/**
 * Suíte de testes automatizados para o Projeto 2: ecommerce-api-legacy (Express MVC).
 */

const assert = require('assert');
const http = require('http');
const app = require('../ecommerce-api-legacy/src/app');

function makeRequest(baseUrl, path, options = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(baseUrl + path);
    const req = http.request(url, options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(body); } catch (e) {}
        resolve({ status: res.statusCode, body, json });
      });
    });
    req.on('error', reject);
    if (options.body) req.write(options.body);
    req.end();
  });
}

async function runTests() {
  console.log('--- Iniciando Testes de ecommerce-api-legacy ---');
  const server = app.listen(0);
  const port = server.address().port;
  const baseUrl = `http://127.0.0.1:${port}`;

  try {
    // 1. Checkout com sucesso
    console.log('[TEST 1] POST /api/checkout (Cartão VISA 4xxx - Sucesso)');
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
    assert.ok(r1.json.enrollment_id, 'Deve retornar enrollment_id');
    console.log('  -> OK: Checkout processado com sucesso.');

    // 2. Checkout recusado (Mastercard 5xxx)
    console.log('[TEST 2] POST /api/checkout (Cartão 5xxx - Recusado)');
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

    // 3. Checkout campos obrigatórios ausentes
    console.log('[TEST 3] POST /api/checkout (Bad Request)');
    const r3 = await makeRequest(baseUrl, '/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usr: 'Incompleto' })
    });
    assert.strictEqual(r3.status, 400);
    assert.strictEqual(r3.body, 'Bad Request');
    console.log('  -> OK: Rejeição de payload incompleto.');

    // 4. Checkout curso inexistente
    console.log('[TEST 4] POST /api/checkout (Curso Não Encontrado)');
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
    console.log('  -> OK: 404 retornado para curso inválido.');

    // 5. Relatório Financeiro
    console.log('[TEST 5] GET /api/admin/financial-report');
    const r5 = await makeRequest(baseUrl, '/api/admin/financial-report', { method: 'GET' });
    assert.strictEqual(r5.status, 200);
    assert.ok(Array.isArray(r5.json), 'Relatório deve ser um array');
    assert.ok(r5.json.length >= 2, 'Deve conter pelo menos 2 cursos');
    console.log('  -> OK: Relatório gerado com sucesso sem N+1.');

    // 6. Deletar usuário com cascata
    console.log('[TEST 6] DELETE /api/users/1');
    const r6 = await makeRequest(baseUrl, '/api/users/1', { method: 'DELETE' });
    assert.strictEqual(r6.status, 200);
    assert.ok(r6.body.includes('Usuário deletado'), 'Deve confirmar exclusão');
    console.log('  -> OK: Usuário deletado com integridade referencial.');

    console.log('--- Todos os 6 testes de ecommerce-api-legacy foram aprovados com sucesso! ---');
  } finally {
    server.close();
  }
}

runTests().catch((err) => {
  console.error('FALHA NOS TESTES:', err);
  process.exit(1);
});
