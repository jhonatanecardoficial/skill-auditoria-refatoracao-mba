# Relatório de Execução de Testes Automatizados

Este documento consolida a metodologia **100% Black-Box E2E sem mocks**, a cobertura de testes funcionais e de segurança (*Red-Team*), e as evidências reais de execução aplicadas aos três projetos refatorados no desafio **Criação de Skills — Refatoração Arquitetural Automatizada (`refactor-arch`)**.

---

## 1. Metodologia Zero-Mock e Visão Geral da Suíte

Nenhum teste desta suíte utiliza `app.test_client()`, `test_config`, bancos `:memory:` substitutos ou simulação de variáveis de ambiente favoráveis:
- Cada aplicação é iniciada em **subprocesso real independente** (`python app.py`, `node src/app.js`, `python seed.py` + `python app.py`) escutando em porta TCP real e gravando em arquivo SQLite real em disco temporário.
- O ambiente de inicialização é explicitamente limpo (`ENVIRONMENT`, `NODE_ENV`, `SECRET_KEY`, `DB_PASS`, `PAYMENT_GATEWAY_KEY`, `SMTP_PASSWORD` removidos) para comprovar comportamento **Fail-Closed** real em produção.
- Além dos contratos funcionais, a suíte executa cadeias reais de ataque (*Red-Team*): **Mass Assignment** (`POST /usuarios` com `"tipo": "admin"`, `POST /api/checkout` com `"role": "admin"` e `POST`/`PUT /users` com `"role": "admin"`), proteção de rotas administrativas (`/admin/reset-db` e `/api/admin/financial-report`), **forja offline de token**, **SQL Injection**, **quantidades negativas/booleanas**, **vazamento PCI-DSS em `stdout`/`stderr`** e inspeção direta dos hashes e papéis nos arquivos `.db` em disco.

| Projeto | Stack Tecnológica | Arquivo de Teste | Suítes / Cenários E2E Reais | Status |
| :--- | :--- | :--- | :---: | :---: |
| **Project 1 (`code-smells-project`)** | Python 3 + Flask | `tests/test_code_smells_project.py` | 5 suítes (2 processos reais + Red-Team) | **100% Aprovado** |
| **Project 2 (`ecommerce-api-legacy`)** | Node.js + Express | `tests/test_ecommerce_api.js` | 12 cenários E2E reais + RBAC/HMAC + PCI-DSS/DB | **100% Aprovado** |
| **Project 3 (`task-manager-api`)** | Python 3 + Flask + SQLAlchemy | `tests/test_task_manager_api.py` | 5 suítes (`seed.py` + `app.py` + tokens assinados) | **100% Aprovado** |

---

## 2. Detalhamento dos Cenários Validados

### 2.1. Projeto 1: `code-smells-project` (2 Servidores Reais em Subprocessos)
- **Servidor A (`python app.py` sem `ENVIRONMENT` e sem `SECRET_KEY`):**
  - **Fail-Closed na Raiz e Health Check:** Confirma `GET /health` retornando `"ambiente": "production"`, sem expor `secret_key` ou `db_path`.
  - **CRUD de Produtos e Tipagem Estrita:** Valida `GET /produtos`, `GET /produtos/busca`, `POST`, `PUT` (incluindo rejeição `400` para categoria inválida e booleanos em `preco`/`estoque`), `DELETE`, `404` pós-exclusão e `preco_min=invalido` retornando `400`.
  - **Defesa contra Mass Assignment (`POST /usuarios`) e Trava Fail-Closed:**
    - Registra usuário anônimo enviando `"tipo": "admin"` -> servidor ignora o campo e grava `"tipo": "cliente"` (verificado via `GET /usuarios/:id` e `POST /login`).
    - Usuário criado faz login e tenta `POST /admin/reset-db` -> bloqueado com **`403 Forbidden`**.
    - Mesmo o administrador legítimo (`admin@loja.com`/`admin123`) tentando `POST /admin/reset-db` sem `ENVIRONMENT` definido recebe **`403 Forbidden`**, mantendo todos os registros intactos.
  - **Backdoor, SQL Injection, Quantidade Negativa e Auditoria do SQLite em Disco:**
    - `POST /admin/query` retorna rigorosamente **`404 Not Found`**.
    - Payloads SQLi em `/produtos/busca` e `/login` são neutralizados por queries parametrizadas.
    - `POST /pedidos` rejeita `quantidade` negativa (`-5`), zero (`0`), booleana (`True`) e `usuario_id` inexistente com `400`, preservando o estoque; atualizações de status via `PUT /pedidos/:id/status` passam por `PedidoService` e `NotificationService`.
    - Leitura direta da tabela `usuarios` no SQLite confirma 100% dos registros com hash `scrypt:`/`pbkdf2:`.
- **Servidor B (`python app.py` com `ENVIRONMENT=testing` e sem `SECRET_KEY`):**
  - Requisição sem Bearer token -> **`401 Unauthorized`**.
  - Tentativa de forja offline de token com antiga chave estática -> **`401 Unauthorized`** (chave efêmera CSPRNG `secrets.token_hex(32)` ativa).
  - Auto-cadastro com `"tipo": "admin"` seguido de login e `POST /admin/reset-db` -> **`403 Forbidden`** mesmo em `testing`.
  - Administrador legítimo (`admin@loja.com`) em `testing` -> **`200 OK`**, zerando tabelas no arquivo SQLite real via `AdminModel`; reenvio do mesmo token após exclusão do registro retorna **`403 Forbidden`** (revalidação no banco).

### 2.2. Projeto 2: `ecommerce-api-legacy` (`node src/app.js` em Subprocesso Real)
- **Configuração Fail-Closed e Chave Efêmera:** Valida em subprocessos limpos que `config.js` assume `nodeEnv: "production"`, `dbPass: ""`, `paymentGatewayKey: ""` e gera `secretKey` efêmera de 64 caracteres hex única por processo (`crypto.randomBytes(32)`).
- **Proteção de `/api/admin/financial-report` (`requireAdmin` + HMAC-SHA256 + DB Revalidation):**
  - Requisição sem token Bearer -> **`401 Unauthorized`**.
  - Requisição com token forjado -> **`401 Unauthorized`**.
  - Aluno criado via `POST /api/checkout` (mesmo enviando `"role": "admin"` no payload público) faz login em `POST /api/login` como `"student"` e tenta acessar `GET /api/admin/financial-report` -> **`403 Forbidden`**.
  - Administrador autenticado (`admin@fullcycle.com.br`) recebe **`200 OK`** com os dados financeiros agregados sem N+1.
- **Proteção contra Exclusão de Admin e Integridade Referencial:** Tentativa de `DELETE /api/users/2` (admin) é bloqueada com **`403 Forbidden`**; `DELETE /api/users/1` (aluno) responde `200 OK` e o relatório financeiro subsequente confirma remoção de receitas e matrículas órfãs.
- **Fluxos Reais de Checkout, Logs PCI-DSS e SQLite em Disco:** Valida cartão VISA (`200`), Mastercard (`400`), payload incompleto (`400`), cartão numérico JSON (`200`), curso inexistente (`404`), mascaramento `************4444` no `stdout` sem vazar cartão completo ou chave, e hashes PBKDF2 + menor privilégio (`role`) para 100% dos usuários no arquivo SQLite real.

### 2.3. Projeto 3: `task-manager-api` (`seed.py` + `app.py` Reais)
- **Execução Real de Seed e Boot:** Popula arquivo SQLite em disco via `python seed.py` (`3 usuários`, `4 categorias`, `10 tasks`) e inicia `python app.py` sem variáveis de ambiente maquiadas.
- **Cobertura Completa de Rotas:** Valida `/`, `/health`, `/tasks` (com `joinedload`), `/tasks/search` (incluindo `400` para `priority=invalido` e `user_id=invalido` e rejeição `400` de booleano em `priority`), `/tasks/stats`, `/users`, `/users/:id/tasks`, `/login`, `/reports/summary`, `/reports/user/:id` e CRUD `/categories` (validação `#RRGGBB`).
- **Tokens Criptográficos, Anti-Mass Assignment e Remoção Total de MD5:** Confirma que `POST /login` emite token assinado via `middlewares/auth_middleware.py` (`itsdangerous` + `SECRET_KEY`, zero `fake-jwt-token-`), `POST /users` com `"role": "admin"` grava `"role": "user"`, `PUT /users/:id` tentando elevar `"role"` retorna **`403 Forbidden`**, nenhuma resposta expõe `"password"`, e 100% das senhas no `.db` utilizam `scrypt:`/`pbkdf2:` (zero MD5).
- **Configuração Fail-Closed e Chave Efêmera:** Confirma `Config.ENVIRONMENT == "production"`, `Config.SMTP_PASSWORD == ""` e geração de `SECRET_KEY` distinta por processo (64 caracteres hex via `secrets.token_hex(32)`).

---

## 3. Registro de Execução dos Testes (Log Oficial Real)

```text
=======================================================
EXECUTANDO: D:\Ecard\MBA\skill-auditoria-refatoracao-mba\venv\Scripts\python.exe -m unittest tests/test_code_smells_project.py
DIRETÓRIO: d:\Ecard\MBA\skill-auditoria-refatoracao-mba
=======================================================
.....
----------------------------------------------------------------------
Ran 5 tests in 5.429s

OK

✅ Sucesso em code-smells-project

=======================================================
EXECUTANDO: node tests/test_ecommerce_api.js
DIRETÓRIO: d:\Ecard\MBA\skill-auditoria-refatoracao-mba
=======================================================
--- Iniciando Testes E2E Reais (Zero Mocks) de ecommerce-api-legacy ---
[TEST 1] Config fail-closed e secretKey efemera sem variaveis de ambiente
  -> OK: config.js fail-closed + CSPRNG confirmado.
[TEST 2] Red-Team GET /api/admin/financial-report sem token -> 401
  -> OK: Acesso anonimo ao relatorio financeiro bloqueado com 401.
[TEST 3] Red-Team GET /api/admin/financial-report com token forjado -> 401
  -> OK: Token forjado rejeitado com 401.
[TEST 4] POST /api/checkout (VISA 4xxx + tentativa role=admin no body)
  -> OK: Checkout processado sobre HTTP real.
[TEST 5] Red-Team Anti-Mass Assignment + RBAC (aluno tentando /api/admin/financial-report -> 403)
  -> OK: Auto-elevacao bloqueada e aluno barrado com 403 no /api/admin/financial-report.
[TEST 6] POST /api/checkout (Cartao 5xxx - Recusado)
  -> OK: Pagamento recusado conforme regra.
[TEST 7] POST /api/checkout (Bad Request)
  -> OK: Rejeicao de payload incompleto.
[TEST 8] POST /api/checkout (Cartao enviado como inteiro JSON)
  -> OK: Cartao numerico tratado sem erro 500.
[TEST 9] POST /api/checkout (Curso Nao Encontrado)
  -> OK: 404 retornado para curso invalido.
[TEST 10] POST /api/login admin + GET /api/admin/financial-report -> 200
  -> OK: Relatorio financeiro protegido respondendo 200 para admin autenticado.
[TEST 11] Protecao contra DELETE /api/users/2 (admin) + DELETE /api/users/1 sem orfaos
  -> OK: Exclusao em cascata comprovada e conta admin preservada.
[TEST 12] Auditoria PCI-DSS no stdout real e PBKDF2/roles no SQLite em disco
  -> OK: Logs PCI-DSS limpos, 100% PBKDF2 e menor privilegio no SQLite real.
--- Todos os 12 testes E2E reais de ecommerce-api-legacy foram aprovados! ---

✅ Sucesso em ecommerce-api-legacy

=======================================================
EXECUTANDO: D:\Ecard\MBA\skill-auditoria-refatoracao-mba\venv\Scripts\python.exe -m unittest tests/test_task_manager_api.py
DIRETÓRIO: d:\Ecard\MBA\skill-auditoria-refatoracao-mba
=======================================================
.....
----------------------------------------------------------------------
Ran 5 tests in 5.123s

OK

✅ Sucesso em task-manager-api

=======================================================
🎉 TODOS OS TESTES DOS 3 PROJETOS FORAM APROVADOS!
=======================================================
```

---

## 4. Conclusão

A execução integral da suíte E2E real sem mocks comprova que:
1. **Zero Quebras de Contrato:** Todos os endpoints preservam contratos funcionais ao subirem em processos reais (`python app.py`, `node src/app.js`, `python seed.py` + `python app.py`).
2. **Zero Anti-Patterns Ativos:** Todos os 14 achados do Projeto 1 (`[F1]`–`[F14]`), 12 achados do Projeto 2 (`[F1]`–`[F12]`) e 12 achados do Projeto 3 (`[F1]`–`[F12]`) — totalizando 38 achados alinhados à escala oficial — foram integralmente corrigidos.
3. **Defesa Real Comprovada em Todas as Rotas `/admin*`:** Tanto `POST /admin/reset-db` (Projeto 1) quanto `GET /api/admin/financial-report` (Projeto 2) exigem autenticação Bearer assinada, papel administrativo revalidado no banco e defesa contra Mass Assignment, enquanto o `task-manager-api` (Projeto 3) emite tokens assinados com `itsdangerous` e opera 100% em MVC sem MD5.
