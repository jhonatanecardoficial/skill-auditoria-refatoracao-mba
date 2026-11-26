# Relatório de Execução de Testes Automatizados

Este documento consolida a metodologia **100% Black-Box E2E sem mocks**, a cobertura de testes funcionais e de segurança (*Red-Team*), e as evidências reais de execução aplicadas aos três projetos refatorados no desafio **Criação de Skills — Refatoração Arquitetural Automatizada (`refactor-arch`)**.

---

## 1. Metodologia Zero-Mock e Visão Geral da Suíte

Nenhum teste desta suíte utiliza `app.test_client()`, `test_config`, bancos `:memory:` substitutos ou simulação de variáveis de ambiente favoráveis:
- Cada aplicação é iniciada em **subprocesso real independente** (`python app.py`, `node src/app.js`, `python seed.py` + `python app.py`) escutando em porta TCP real e gravando em arquivo SQLite real em disco temporário.
- O ambiente de inicialização é explicitamente limpo (`ENVIRONMENT`, `NODE_ENV`, `SECRET_KEY`, `DB_PASS`, `PAYMENT_GATEWAY_KEY`, `SMTP_PASSWORD` removidos) para comprovar comportamento **Fail-Closed** real em produção.
- Além dos contratos funcionais, a suíte executa cadeias reais de ataque (*Red-Team*): **Mass Assignment** (`POST /usuarios` com `"tipo": "admin"` e `POST`/`PUT /users` com `"role": "admin"`), **forja offline de token**, **SQL Injection**, **quantidades negativas/booleanas**, **vazamento PCI-DSS em `stdout`/`stderr`** e inspeção direta dos hashes nos arquivos `.db` em disco.

| Projeto | Stack Tecnológica | Arquivo de Teste | Suítes / Cenários E2E Reais | Status |
| :--- | :--- | :--- | :---: | :---: |
| **Project 1 (`code-smells-project`)** | Python 3 + Flask | `tests/test_code_smells_project.py` | 5 suítes (2 processos reais + Red-Team) | **100% Aprovado** |
| **Project 2 (`ecommerce-api-legacy`)** | Node.js + Express | `tests/test_ecommerce_api.js` | 9 cenários E2E reais + auditoria PCI-DSS/DB | **100% Aprovado** |
| **Project 3 (`task-manager-api`)** | Python 3 + Flask + SQLAlchemy | `tests/test_task_manager_api.py` | 5 suítes (`seed.py` + `app.py` + Red-Team) | **100% Aprovado** |

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
    - `POST /pedidos` rejeita `quantidade` negativa (`-5`), zero (`0`), booleana (`True`) e `usuario_id` inexistente com `400`, preservando o estoque.
    - Leitura direta da tabela `usuarios` no SQLite confirma 100% dos registros com hash `scrypt:`/`pbkdf2:`.
- **Servidor B (`python app.py` com `ENVIRONMENT=testing` e sem `SECRET_KEY`):**
  - Requisição sem Bearer token -> **`401 Unauthorized`**.
  - Tentativa de forja offline de token com antiga chave estática -> **`401 Unauthorized`** (chave efêmera CSPRNG `secrets.token_hex(32)` ativa).
  - Auto-cadastro com `"tipo": "admin"` seguido de login e `POST /admin/reset-db` -> **`403 Forbidden`** mesmo em `testing`.
  - Administrador legítimo (`admin@loja.com`) em `testing` -> **`200 OK`**, zerando tabelas no arquivo SQLite real via `AdminModel`; reenvio do mesmo token após exclusão do registro retorna **`403 Forbidden`** (revalidação no banco).

### 2.2. Projeto 2: `ecommerce-api-legacy` (`node src/app.js` em Subprocesso Real)
- **Configuração Fail-Closed:** Valida em subprocesso limpo que `config.js` assume `nodeEnv: "production"`, `dbPass: ""` e `paymentGatewayKey: ""`.
- **Fluxos Reais de Checkout:** Cartão VISA string (`200`, `enrollment_id`), Mastercard (`400`, `"Pagamento recusado"`), payload incompleto (`400`, `"Bad Request"`), cartão numérico JSON tratado sem erro `500` (`200`) e curso inexistente (`404`).
- **Relatório Financeiro e Exclusão em Cascata Sem Órfãos:** Valida `GET /api/admin/financial-report`, executa `DELETE /api/users/1` e consulta novamente o relatório comprovando remoção integral de receitas e matrículas do usuário excluído.
- **Auditoria PCI-DSS em `stdout`/`stderr` e SQLite em Disco:** Confirma presença de `************4444`, ausência total de números completos de cartão ou chaves de gateway nos logs reais do servidor, e valida formato `salt:hash` PBKDF2 para 100% dos usuários gravados no `.db`.

### 2.3. Projeto 3: `task-manager-api` (`seed.py` + `app.py` Reais)
- **Execução Real de Seed e Boot:** Popula arquivo SQLite em disco via `python seed.py` (`3 usuários`, `4 categorias`, `10 tasks`) e inicia `python app.py` sem variáveis de ambiente maquiadas.
- **Cobertura Completa de Rotas:** Valida `/`, `/health`, `/tasks` (com `joinedload`), `/tasks/search` (incluindo `400` para `priority=invalido` e `user_id=invalido` e rejeição `400` de booleano em `priority`), `/tasks/stats`, `/users`, `/users/:id/tasks`, `/login`, `/reports/summary`, `/reports/user/:id` e CRUD `/categories` (validação `#RRGGBB`).
- **Defesa contra Mass Assignment e Remoção Total de MD5:** Confirma que `POST /users` com `"role": "admin"` grava `"role": "user"`, que `PUT /users/:id` tentando elevar `"role"` retorna **`403 Forbidden`**, que nenhuma resposta expõe `"password"`, e que 100% das senhas no `.db` utilizam `scrypt:`/`pbkdf2:` (zero MD5).
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
Ran 5 tests in 6.268s

OK

✅ Sucesso em code-smells-project

=======================================================
EXECUTANDO: node tests/test_ecommerce_api.js
DIRETÓRIO: d:\Ecard\MBA\skill-auditoria-refatoracao-mba
=======================================================
--- Iniciando Testes E2E Reais (Zero Mocks) de ecommerce-api-legacy ---
[TEST 1] Config fail-closed sem variaveis de ambiente
  -> OK: config.js fail-closed confirmado.
[TEST 2] POST /api/checkout (Cartao VISA 4xxx - Sucesso)
  -> OK: Checkout processado sobre HTTP real.
[TEST 3] POST /api/checkout (Cartao 5xxx - Recusado)
  -> OK: Pagamento recusado conforme regra.
[TEST 4] POST /api/checkout (Bad Request)
  -> OK: Rejeicao de payload incompleto.
[TEST 5] POST /api/checkout (Cartao enviado como inteiro JSON)
  -> OK: Cartao numerico tratado sem erro 500.
[TEST 6] POST /api/checkout (Curso Nao Encontrado)
  -> OK: 404 retornado para curso invalido.
[TEST 7] GET /api/admin/financial-report
  -> OK: Relatorio agregado gerado sem N+1.
[TEST 8] DELETE /api/users/1 e verificacao de zero orfaos
  -> OK: Exclusao em cascata comprovada no relatorio real.
[TEST 9] Auditoria PCI-DSS no stdout real e PBKDF2 no SQLite em disco
  -> OK: Logs PCI-DSS limpos e 100% PBKDF2 no arquivo SQLite real.
--- Todos os 9 testes E2E reais de ecommerce-api-legacy foram aprovados! ---

✅ Sucesso em ecommerce-api-legacy

=======================================================
EXECUTANDO: D:\Ecard\MBA\skill-auditoria-refatoracao-mba\venv\Scripts\python.exe -m unittest tests/test_task_manager_api.py
DIRETÓRIO: d:\Ecard\MBA\skill-auditoria-refatoracao-mba
=======================================================
.....
----------------------------------------------------------------------
Ran 5 tests in 6.437s

OK

✅ Sucesso em task-manager-api

=======================================================
🎉 TODOS OS TESTES DOS 3 PROJETOS FORAM APROVADOS!
=======================================================
```

---

## 4. Conclusão

A execução integral da suíte E2E real sem mocks comprova que:
1. **Zero Quebras de Contrato:** Todos os endpoints originais preservam status codes e payloads esperados pelos consumidores ao subirem em processos reais (`python app.py`, `node src/app.js`, `python seed.py` + `python app.py`).
2. **Zero Anti-Patterns Ativos:** Todos os 14 achados do Projeto 1 (`[F1]`–`[F14]`), 10 achados do Projeto 2 (`[F1]`–`[F10]`) e 11 achados do Projeto 3 (`[F1]`–`[F11]`) foram devidamente sanados, com eliminação definitiva de MD5, fallbacks estáticos e SQL em controllers.
3. **Defesa Real Comprovada (Fail-Closed & Anti-Mass Assignment):** Cadastros públicos não aceitam privilégios administrativos (`tipo`/`role`), ambientes sem `ENVIRONMENT` definido bloqueiam `/admin/reset-db` (`403 Forbidden`), chaves ausentes geram entropia aleatória via CSPRNG e `@require_admin` revalida usuário e papel diretamente no banco de dados.
