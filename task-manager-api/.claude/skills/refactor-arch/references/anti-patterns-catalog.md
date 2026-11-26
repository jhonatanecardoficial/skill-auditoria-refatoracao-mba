# Catálogo de Anti-Patterns, Code Smells e APIs Deprecated

Este catálogo orienta a **Fase 2 (Auditoria Arquitetural)** da skill `refactor-arch`. Cada achado deve ser classificado estritamente de acordo com a escala oficial de severidades descrita abaixo.

---

## Escala de Severidades

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex.: credenciais hardcoded, SQL Injection, endpoints `/admin` sem autenticação, Mass Assignment de privilégios) ou violam completamente a separação de responsabilidades (ex.: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex.: lógicas de negócio pesadas presas dentro de Controllers / Fat Routes, forte acoplamento / Callback Hell sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex.: Queries N+1 no banco de dados, uso inadequado de middlewares / ausência de erro centralizado, validações ausentes nas rotas / registros órfãos, APIs deprecated).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, código morto/imports não utilizados, lógica booleana redundante ou "magic numbers" soltos pelo código.

---

## Catálogo de Anti-Patterns e Code Smells

### 1. SQL Injection (CRITICAL)
- **Descrição:** Montagem de instruções SQL através de interpolação ou concatenação de strings com dados oriundos de requisições de usuário, sem uso de queries parametrizadas (placeholders `?` ou `:param`).
- **Sinais de Detecção:**
  - Python: `"SELECT * FROM ... WHERE id = " + str(id)`, `f"INSERT INTO ... VALUES ('{nome}')"`.
  - Node.js: `` `SELECT * FROM ... WHERE id = ${id}` ``, `"UPDATE ... WHERE id = " + id`.
- **Impacto:** Permite extração, alteração e destruição não autorizada de dados do banco.
- **Recomendação:** Substituir por consultas preparadas com parâmetros (`cursor.execute("... WHERE id = ?", (id,))`) ou ORM.

### 2. God Class / God Module (CRITICAL)
- **Descrição:** Classe ou módulo único que centraliza múltiplas responsabilidades desconexas (gerenciamento de conexão, criação de schemas, definição de rotas HTTP, regras de negócio e formatação de resposta).
- **Sinais de Detecção:**
  - Arquivo único com mais de 130-300 linhas manipulando múltiplos domínios (ex.: produtos, usuários, pedidos, relatórios, pagamentos).
  - Classes/módulos acumulando `initDb()`, `setupRoutes()`, `processCheckout()`, `generateReport()`.
- **Impacto:** Alto acoplamento, impossibilidade de testes unitários isolados, alto risco de regressões a cada alteração.
- **Recomendação:** Decompor em camadas MVC: Models por domínio, Controllers com responsabilidade única e rotas desacopladas.

### 3. Hardcoded Secrets, Credentials and Fake Unsigned Tokens (CRITICAL)
- **Descrição:** Chaves secretas, senhas de banco de dados, senhas SMTP, chaves de gateways, **fallbacks estáticos previsíveis** ou **tokens de autenticação literais sem assinatura criptográfica** gravados diretamente no código-fonte.
- **Sinais de Detecção:**
  - `SECRET_KEY = "minha-chave-super-secreta-123"` ou `os.getenv("SECRET_KEY", "dev-fallback-key")`
  - `self.email_password = 'senha123'`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_..."`
  - Emissão de tokens sem assinatura verificável: `f"fake-jwt-token-{user.id}"`.
- **Impacto:** Vazamento de credenciais críticas em controle de versão, forja trivial ou offline de sessões/tokens administrativos e impossibilidade de rotação de chaves por ambiente.
- **Recomendação:** Carregar exclusivamente via variáveis de ambiente (`config/settings.py` ou `config.js`), gerando chaves efêmeras com CSPRNG (`secrets.token_hex(32)` / `crypto.randomBytes(32)`) quando `SECRET_KEY` estiver ausente, `""` para credenciais externas opcionais, e assinar todos os tokens com HMAC/TimedSerializer.

### 4. Weak Cryptography and Sensitive Data Exposure (CRITICAL)
- **Descrição:** Armazenamento de senhas em texto puro ou uso de funções criptográficas inseguras/quebradas (ex.: MD5 simples sem salt, hashing customizado rudimentar em Base64), além de vazamento de senhas em JSON ou dados de cartão/chaves nos logs (violação PCI-DSS).
- **Sinais de Detecção:**
  - `hashlib.md5(pwd.encode()).hexdigest()`, senhas em texto plano em seeds (`'123'`, `'admin123'`).
  - Serialização contendo `'password': self.password` ou retorno de senhas no JSON de resposta.
  - Funções de hashing truncadas sem salt (`badCrypto`) ou `console.log(\`Processando cartão ${cc}\`)`.
- **Impacto:** Comprometimento em massa de credenciais, violação de normas PCI-DSS/LGPD e vulnerabilidade a rainbow tables.
- **Recomendação:** Utilizar algoritmos modernos com salt (PBKDF2/scrypt via Werkzeug ou `crypto.pbkdf2Sync`), omitir senhas de qualquer resposta JSON e mascarar números de cartão nos logs (`************4444`).

### 5. Unprotected Administrative Endpoints (`/admin*`), Arbitrary SQL Execution, Mass Assignment & Fail-Open Defaults (CRITICAL)
- **Descrição:** Qualquer endpoint administrativo exposto sem autenticação/autorização estrita (como `/admin/query`, `/admin/reset-db` ou `/api/admin/financial-report`), execução SQL arbitrária, brechas de **Mass Assignment / Escalação de Privilégios** onde cadastros públicos aceitam `tipo`/`role` do payload, e **defaults fail-open** que assumem `"development"` quando `ENVIRONMENT`/`NODE_ENV` não está definido.
- **Sinais de Detecção:**
  - **Heurística Universal de Rotas:** qualquer rota cujo path contenha `/admin` (ou `/internal`, `/debug`) sem middleware explícito de autenticação e autorização (`@require_admin` / `requireAdmin`), **independentemente da stack** ou de possuir outros achados (como N+1) no mesmo endpoint.
  - `@app.route('/admin/query')` executando `cursor.execute(request.json['sql'])`.
  - Cadastro público lendo papel do payload: `tipo = dados.get("tipo", "cliente")` ou `role = data.get("role", "user")`.
  - Default inseguro de ambiente: `os.getenv("ENVIRONMENT", "development")` ou `process.env.NODE_ENV || "development"`.
- **Impacto:** Permite acesso público a relatórios financeiros confidenciais de clientes, auto-cadastro anônimo como administrador e destruição total do banco de dados mesmo sem `ENVIRONMENT` configurado.
- **Recomendação:** Remover backdoors de execução SQL arbitrária (404), proteger **todas** as rotas `/admin*` com `@require_admin` / `requireAdmin` + revalidação do papel no banco, proibir `tipo`/`role` em cadastros públicos e adotar default *fail-closed* `"production"` para `ENVIRONMENT`/`NODE_ENV`.

### 6. Business Logic in Controllers / Fat Routes (HIGH)
- **Descrição:** Controllers ou manipuladores de rota executando cálculos de regras de negócio, manipulação direta de ORM (`db.session`), verificação de estoque ou envio de notificações (email, SMS) sem separação em Services/Controllers.
- **Sinais de Detecção:**
  - Arquivos de rota (`routes/*.py`) acumulando dezenas/centenas de linhas com validações e queries diretas sem `controllers/`.
  - Controllers executando SQL direto ou despachando notificações inline.
- **Impacto:** Dificuldade de reutilização, controllers/rotas inflados e impossibilidade de testar regras de negócio isoladamente.
- **Recomendação:** Isolar regras de domínio em Services, persistência exclusivamente em Models e controle HTTP em Controllers enxutos.

### 7. Tight Coupling, Callback Hell & Global Mutable State (HIGH)
- **Descrição:** Encadeamento de múltiplos callbacks aninhados (Callback Pyramid em Node.js) ou compartilhamento de variáveis globais mutáveis sem controle de ciclo de vida, concorrência ou limite de tamanho.
- **Sinais de Detecção:**
  - Callback pyramid com 3+ níveis aninhados (`db.get -> db.get -> db.run -> db.run`).
  - `globalCache = {}`, `totalRevenue = 0`, `db_connection = None` global compartilhado sem context manager ou `BoundedCache`.
- **Impacto:** Risco de memory leaks, race conditions, corrupção de estado em concorrência e código ilegível.
- **Recomendação:** Refatorar para Promises / `async/await`, gerenciar conexões por ciclo de requisição (`flask.g` / ORM session) e encapsular caches com limite de tamanho.

### 8. N+1 Query Problem (MEDIUM)
- **Descrição:** Execução de consultas SQL em loop para buscar dados relacionados em listagens ou relatórios gerenciais.
- **Sinais de Detecção:**
  - `for row in pedidos: cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ...", ...)`
  - `courses.forEach(c => db.all("SELECT * FROM enrollments WHERE course_id = ?"))`
  - `for t in tasks: User.query.get(t.user_id)` dentro de listagens/relatórios.
- **Impacto:** Explosão de consultas ($1 + N$ ou $1 + C + 2CE$), latência severa e saturação de I/O.
- **Recomendação:** Utilizar consultas únicas com `LEFT JOIN` / agregações (`GROUP BY`, `SUM`) ou `joinedload` no ORM.

### 9. Deprecated APIs and Outdated Patterns (MEDIUM)
- **Descrição:** Uso de métodos, funções de data ou chamadas de ORM obsoletas e descontinuadas nas versões modernas da linguagem/framework.
- **Sinais de Detecção e Equivalentes Modernos:**
  - **Python `datetime.utcnow()`:** Obsoleto desde o Python 3.12 por gerar datetime naive sem timezone. *Substituto:* `datetime.now(timezone.utc)`.
  - **SQLAlchemy 1.x `Model.query.get(id)`:** Legado e depreciado no SQLAlchemy 2.0. *Substituto:* `db.session.get(Model, id)`.
- **Impacto:** Emissão contínua de `DeprecationWarning` e quebras em atualizações futuras do runtime.
- **Recomendação:** Migrar sistematicamente para as APIs modernas com timezone explícito e `db.session.get`.

### 10. Missing Centralized Error Handling & Bare Excepts (MEDIUM)
- **Descrição:** Uso de blocos `except:` sem classe de exceção especificada (capturando inclusive `SystemExit` e `KeyboardInterrupt`), retornos de erro em texto cru ou duplicação de `try/except` vazando `str(exc)` interno em respostas HTTP 500.
- **Sinais de Detecção:**
  - `except:` vazio em rotas/helpers; retornos `res.status(500).send("Erro DB")` ou `return jsonify({'erro': str(e)}), 500`.
- **Impacto:** Mascaramento silencioso de falhas, violação DRY e vazamento de detalhes internos de stack/banco ao cliente.
- **Recomendação:** Implementar handlers globais (`@app.errorhandler` no Flask, `app.use(errorHandler)` no Express) logando o stack no servidor e respondendo JSON uniforme.

### 11. Magic Numbers, Poor Naming, Dead Imports & Redundant Booleans (LOW)
- **Descrição:** Literais numéricos/strings mágicos dispersos sem constantes nomeadas (`10000`, `5000`, `len < 2`), variáveis crípticas (`u`, `e`, `cid`, `cc`), imports não utilizados no topo ou dentro de funções (`import uuid`), `type(x) == list` e condicionais `if cond: return True else: return False`.
- **Sinais de Detecção:**
  - `let u = req.body.usr; let cc = req.body.card;`
  - Imports mortos (`import sys, math, hashlib`), checagem com `type(...) == list` em vez de `isinstance(...)`.
- **Impacto:** Baixa legibilidade, ruído no código e dificuldade de manutenção colaborativa.
- **Recomendação:** Extrair constantes semânticas, usar nomes descritivos, remover código morto e simplificar expressões booleanas.

### 12. Missing Route Validation, Orphan Records & DRY Violations (MEDIUM)
- **Descrição:** Falta de validação e coerção segura em query parameters ou payloads (`float(preco_min)`, `int(priority)`, quantidades negativas), exclusões de registros pai deixando registros filhos órfãos sem `FOREIGN KEY` / deleção em cascata, e duplicação de regras já existentes em `utils/helpers.py`.
- **Sinais de Detecção:**
  - Conversão direta sem tratamento devolvendo HTTP 500 em vez de 400 (`?priority=abc`, `?preco_min=abc`).
  - `DELETE FROM users WHERE id = ?` sem remover `enrollments`/`payments` vinculados nem habilitar `PRAGMA foreign_keys = ON;`.
  - Rotas reescrevendo validações de email/cor/data em vez de importar as funções de `utils/helpers.py`.
- **Impacto:** Crashes 500 evitáveis, corrupção da integridade referencial do banco e regras divergentes entre endpoints.
- **Recomendação:** Validar tipos/faixas retornando HTTP 400, garantir integridade referencial em cascata/transação e reutilizar helpers centralizados.
