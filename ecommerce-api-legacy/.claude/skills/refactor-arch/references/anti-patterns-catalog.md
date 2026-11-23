# Catálogo de Anti-Patterns, Code Smells e APIs Deprecated

Este catálogo orienta a **Fase 2 (Auditoria Arquitetural)** da skill `refactor-arch`. Cada achado deve ser classificado de acordo com a severidade e os critérios técnicos descritos abaixo.

---

## Escala de Severidades

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex.: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex.: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex.: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex.: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas, APIs deprecated).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

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
  - Arquivo único com mais de 250-300 linhas manipulando múltiplos domínios (ex.: produtos, usuários, pedidos, logs).
  - Classes contendo métodos como `initDb()`, `setupRoutes()`, `processPayment()`, `generateReport()`.
- **Impacto:** Alto acoplamento, impossibilidade de testes unitários isolados, alto risco de regressões a cada alteração.
- **Recomendação:** Decompor em camadas MVC: Models por domínio, Controllers com responsabilidade única e rotas desacopladas.

### 3. Hardcoded Secrets and Credentials (CRITICAL)
- **Descrição:** Chaves secretas, senhas de banco de dados, tokens de autenticação ou chaves de gateways gravadas diretamente no código-fonte.
- **Sinais de Detecção:**
  - `SECRET_KEY = "minha-chave-super-secreta-123"`
  - `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_..."`
- **Impacto:** Vazamento de credenciais críticas em controle de versão, impossibilidade de rotação de chaves por ambiente.
- **Recomendação:** Mover todas as credenciais para variáveis de ambiente carregadas via módulo de configuração (`config/settings.py` ou `.env`).

### 4. Weak Cryptography and Password Exposure (CRITICAL)
- **Descrição:** Armazenamento de senhas em texto puro ou uso de funções criptográficas inseguras/quebradas (ex.: MD5 simples sem salt, hashing customizado rudimentar), além de vazamento de senhas em endpoints públicos.
- **Sinais de Detecção:**
  - `hashlib.md5(pwd.encode()).hexdigest()`
  - Serialização contendo `'password': self.password` ou retorno de senhas no JSON de resposta.
  - Funções de hashing baseadas em base64 repetido (`badCrypto`).
- **Impacto:** Comprometimento em massa de credenciais de usuários e vulnerabilidade a ataques de dicionário e rainbow tables.
- **Recomendação:** Utilizar algoritmos modernos de derivação de chaves (bcrypt/Argon2/PBKDF2) e omitir senhas de qualquer serialização de resposta (`to_dict`).

### 5. Arbitrary SQL Execution Endpoints (CRITICAL)
- **Descrição:** Endpoints de administração ou utilitários expostos que recebem comandos SQL arbitrários do cliente e os executam diretamente no banco.
- **Sinais de Detecção:**
  - `@app.route('/admin/query')` executando `cursor.execute(request.json['sql'])`.
  - Rotas desprotegidas executando `DELETE FROM ...` geral.
- **Impacto:** Permite destruição total do banco de dados por qualquer cliente da API.
- **Recomendação:** Remover endpoints de execução arbitrária e encapsular operações administrativas em rotas restritas e seguras.

### 6. Business Logic in Controllers / Route Handlers (HIGH)
- **Descrição:** Controllers ou manipuladores de rota executando cálculos de regras de negócio, verificação de estoque, regras de precificação, despacho de pagamentos ou envio de notificações (email, SMS).
- **Sinais de Detecção:**
  - Controllers executando loops para calcular totais, descontar estoque e despachar múltiplos canais de notificação.
  - Mistura de código de serialização HTTP (`jsonify`, `res.json`) com lógicas de domínio.
- **Impacto:** Dificuldade de reutilização de lógicas de negócio, controllers inflados e impossibilidade de testar regras sem mockar o framework HTTP.
- **Recomendação:** Isolar as regras de negócio em Serviços de Domínio ou nos respectivos Models.

### 7. Tight Coupling & Callback Hell / Spaghetti Async Flow (HIGH)
- **Descrição:** Encadeamento de múltiplos callbacks aninhados (em Node.js) ou acoplamento direto a variáveis globais mutáveis sem injeção de dependência.
- **Sinais de Detecção:**
  - Callback pyramid (mais de 3 níveis de callbacks aninhados para queries consecutivas).
  - `globalCache = {}`, `totalRevenue = 0` compartilhados entre requisições.
- **Impacto:** Código ilegível, alta propensão a race conditions e vazamento de memória em concorrência.
- **Recomendação:** Refatorar para Promises e `async/await` com tratamento estruturado de erros via `try/catch`.

### 8. N+1 Query Problem (MEDIUM)
- **Descrição:** Execução de consultas SQL em loop para buscar dados relacionados (ex.: para cada pedido na lista, disparar uma query individual para itens e outra para o nome do produto).
- **Sinais de Detecção:**
  - `for row in pedidos: cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + ...)`
  - `courses.forEach(c => db.all("SELECT * FROM enrollments WHERE course_id = ?"))`
- **Impacto:** Degradação severa de desempenho conforme a base de dados cresce.
- **Recomendação:** Utilizar consultas com `JOIN` (`INNER JOIN`, `LEFT JOIN`) ou carregar dados em lote através de cláusulas `WHERE IN (...)`.

### 9. Deprecated APIs and Outdated Patterns (MEDIUM)
- **Descrição:** Uso de métodos, bibliotecas ou assinaturas de framework descontinuadas ou não recomendadas nas versões modernas.
- **Sinais de Detecção e Equivalentes Modernos:**
  - **Python `datetime.utcnow()`:** Obsoleto desde o Python 3.12 por não carregar timezone (naive datetime).  
    *Equivalente moderno:* `datetime.now(timezone.utc)` da biblioteca `datetime`.
  - **SQLAlchemy 1.x `Model.query.get(id)`:** Padrão herdado de versões legadas do Flask-SQLAlchemy.  
    *Equivalente moderno:* `db.session.get(Model, id)`.
  - **Node.js Express rotas com callbacks síncronos sem tratamento de rejeição:**  
    *Equivalente moderno:* Funções de rota `async (req, res, next)` repassando erros para middlewares centralizados de erro.
- **Impacto:** Deprecation warnings em logs, quebras em upgrades de versão e comportamento imprevisível com timezones.
- **Recomendação:** Substituir sistematicamente pelas APIs canônicas e modernas.

### 10. Missing Centralized Error Handling & Bare Excepts (MEDIUM)
- **Descrição:** Captura genérica de erros com `except:` vazio (que captura até `KeyboardInterrupt` e `SystemExit`), mascaramento de stack traces com mensagens vagas (`{'error': 'Erro interno'}`) e ausência de middleware centralizado de erros.
- **Sinais de Detecção:**
  - `except:` sem tipo de exceção especificado.
  - Blocos `try/except` repetidos com a mesma resposta `500` em cada função de controller.
- **Impacto:** Dificuldade extrema de depuração e inconsistência de formato de erros para o cliente.
- **Recomendação:** Definir handlers globais de erro (`@app.errorhandler` no Flask, `app.use((err, req, res, next) => ...)` no Express).

### 11. Magic Numbers and Poor Naming (LOW)
- **Descrição:** Valores literais mágicos dispersos no código sem constantes nomeadas (ex.: `priority < 1 or priority > 5`, `len(nome) < 2`), além de identificadores crípticos de 1 ou 2 letras (`u`, `e`, `p`, `cid`, `cc`).
- **Sinais de Detecção:**
  - `let u = req.body.usr; let p = req.body.pwd;`
  - Números sem contexto explicativo (`997.00`, `10000`, `200`).
- **Impacto:** Dificulta a legibilidade e a manutenção colaborativa do código.
- **Recomendação:** Utilizar nomes descritivos e constantes/enums nomeados.
