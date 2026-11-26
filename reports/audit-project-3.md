================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack: Python 3 + Flask + SQLAlchemy
Files: 11 analyzed | ~1150 lines of code

## Summary
CRITICAL: 4 | HIGH: 1 | MEDIUM: 5 | LOW: 2

## Findings

### [F1] [CRITICAL] Criptografia de Senhas Insegura com MD5
File: models/user.py:27-32
Description: Os métodos `set_password` e `check_password` utilizam MD5 puro sem salt (`hashlib.md5(pwd.encode()).hexdigest()`), algoritmo criptograficamente quebrado e vulnerável a rainbow tables e colisões imediatas.
Impact: Em caso de comprometimento ou leitura da base, todas as senhas são recuperadas em segundos.
Recommendation: Migrar integralmente para `werkzeug.security.generate_password_hash` e `check_password_hash` (PBKDF2/scrypt), removendo `hashlib` e MD5 do model.

### [F2] [CRITICAL] Exposição de Senhas nas Respostas da API
File: models/user.py:16-25, routes/user_routes.py:33
Description: O método `to_dict()` da classe `User` inclui explicitamente `'password': self.password` no JSON retornado em consultas e listagens de usuários.
Impact: Qualquer consumidor dos endpoints de usuário recebe os hashes das contas, facilitando ataques offline.
Recommendation: Remover definitivamente o atributo `password` de `to_dict()` e de todas as respostas JSON.

### [F3] [CRITICAL] Hardcoded Secret Key, Credenciais SMTP em Texto Puro e Token Sem Assinatura
File: app.py:13, services/notification_service.py:7-10, routes/user_routes.py:210
Description: A `SECRET_KEY` está gravada em texto claro no `app.py` (`'super-secret-key-123'`), `NotificationService` mantém `self.email_password = 'senha123'` hardcoded, e `POST /login` devolve token literal previsível sem assinatura (`f'fake-jwt-token-{user.id}'`).
Impact: Exposição de segredos de infraestrutura no repositório, forja trivial de tokens de usuário e impossibilidade de rotação de credenciais por ambiente.
Recommendation: Externalizar configurações para `config/settings.py` com comportamento fail-closed (`secrets.token_hex(32)` e SMTP via env), e emitir tokens assinados criptograficamente via `middlewares/auth_middleware.py`.

### [F4] [CRITICAL] Mass Assignment e Escalação de Privilégio em Rotas Públicas de Usuário
File: routes/user_routes.py:52, 71-78, 119-123
Description: O cadastro público `POST /users` aceita o campo `role` diretamente do payload JSON (permitindo auto-cadastro como `'admin'` ou `'manager'`) e `PUT /users/:id` permite alterar `role` para `'admin'` sem autenticação.
Impact: Qualquer usuário anônimo consegue se auto-promover a administrador da aplicação.
Recommendation: Fixar `role = "user"` em `POST /users` ignorando privilégios vindos do payload e bloquear alteração de `role` em `PUT /users/:id` com HTTP 403.

### [F5] [HIGH] Fat Routes e Violação de Separação de Responsabilidades (MVC)
File: routes/task_routes.py:86-223, routes/report_routes.py:13-155, routes/user_routes.py:42-155
Description: Embora existam diretórios `models/` e `routes/`, as rotas concentram validações manuais extensas, manipulação direta de transações (`db.session.add`, `db.session.commit`), formatação de relatórios e regras de negócio sem nenhuma camada `controllers/` ou `config/`.
Impact: Alto acoplamento entre HTTP e persistência, violando o padrão MVC e impedindo testes unitários das regras sem o runtime Flask.
Recommendation: Extrair `config/settings.py`, `controllers/*.py` e `middlewares/error_handler.py`, deixando Blueprints apenas como mapeadores HTTP.

### [F6] [MEDIUM] N+1 Query Problem em Listagens e Relatórios
File: routes/task_routes.py:41-58, routes/report_routes.py:53-68, 159-163, routes/user_routes.py:13-24
Description: Em `GET /tasks`, para cada tarefa são executadas queries individuais para buscar usuário e categoria; em `/reports/summary` e `/categories`, disparam-se novas consultas para cada usuário e cada categoria.
Impact: Multiplicação de round-trips ao SQLite ($1 + 2N$ e $1 + U$), gerando latência crescente com a base de dados.
Recommendation: Utilizar `joinedload` do SQLAlchemy para eager loading de relacionamentos e contagens agregadas.

### [F7] [MEDIUM] Uso de APIs Deprecated e Padrões Obsoletos
File: models/user.py:14, models/task.py:15-16, routes/task_routes.py:31, 42, 67, services/notification_service.py:35, utils/helpers.py:38, seed.py:64
Description: Uso generalizado de `datetime.utcnow()` (obsoleto desde o Python 3.12 por produzir datetimes naive) e `Model.query.get(id)` (depreciado no SQLAlchemy 2.0).
Impact: Emissão contínua de `DeprecationWarning` e risco de erro em comparações de timezone e upgrades de dependências.
Recommendation: Substituir por `datetime.now(timezone.utc)` e `db.session.get(Model, id)`.

### [F8] [MEDIUM] Captura Genérica de Exceções (Bare Except) e Ausência de Middleware Centralizado
File: routes/task_routes.py:62, 134, 204, 236, routes/user_routes.py:130, 151, routes/report_routes.py:184, 205, 219, utils/helpers.py:46, 49, 88
Description: Pelo menos 12 blocos `except:` sem classe de exceção capturam inclusive exceções de sistema sem registrar logs, acompanhados de tratamento de erro disperso nas rotas.
Impact: Ocultação silenciosa de falhas críticas e dificuldade extrema de diagnóstico em produção.
Recommendation: Capturar exceções específicas (`ValueError`, `TypeError`), registrar stack traces com `logging` e adotar `@app.errorhandler` em `middlewares/error_handler.py`.

### [F9] [MEDIUM] Ausência de Validação de Tipos em Filtros de Busca e Risco de Erro 500
File: routes/task_routes.py:241-271
Description: O endpoint `GET /tasks/search` executa `int(priority)` e `int(user_id)` diretamente sobre query parameters sem validação de erro, além de aceitar booleanos disfarçados de inteiros em `priority`.
Impact: Inputs malformados (`?priority=invalido`) derrubam a requisição com HTTP 500 em vez de responder `400 Bad Request`.
Recommendation: Validar coerção numérica e rejeitar booleanos na camada Controller retornando HTTP 400 descritivo.

### [F10] [MEDIUM] Duplicação de Validações (Violação DRY) e Subutilização de Helpers
File: utils/helpers.py:58-107, routes/task_routes.py:86-154, routes/report_routes.py:166-207
Description: As rotas reimplementam validações de título, status, prioridade, regex de email e datas em vez de reutilizar as funções existentes em `utils/helpers.py`, enquanto `is_valid_color` aceita strings inválidas de 7 chars (`#zzzzzz`) e sequer é chamada na criação de categorias.
Impact: Regras divergentes entre rotas e validação de cor hexadecimal ineficaz.
Recommendation: Validar cor com regex estrito `^#[0-9a-fA-F]{6}$` e integrar os helpers diretamente nos Controllers.

### [F11] [LOW] Lógica Booleana Redundante e Verificações de Tipo Não-Idiomáticas
File: models/user.py:34-38, models/task.py:38-60, utils/helpers.py:19-23, 52-55, 103
Description: Métodos como `is_admin`, `validate_status`, `is_overdue`, `validate_email` e `is_valid_color` usam blocos `if ...: return True else: return False`, além de checagem `type(tags) == list` em vez de `isinstance`.
Impact: Complexidade ciclomática desnecessária e violação de boas práticas Python (PEP 8).
Recommendation: Retornar expressões booleanas diretamente e adotar `isinstance(tags, list)`.

### [F12] [LOW] Magic Numbers, Imports Mortos/Fora de Escopo e Prints de Debug
File: utils/helpers.py:1-7, 31-34, app.py:7, routes/task_routes.py:93, 96, 111, 145
Description: Há 5 imports não utilizados em `helpers.py` (`os`, `json`, `sys`, `math`, `hashlib`), imports mortos em `app.py`, `import uuid` dentro da função `generate_id()`, magic numbers (`< 3`, `> 200`, `1..5`) espalhados nas rotas e `print()` usados como log.
Impact: Ruído estrutural, baixa manutenibilidade e ausência de níveis adequados de logging.
Recommendation: Remover imports mortos, centralizar constantes em `helpers.py`, mover imports para o topo e adotar `logging`.

================================
Total: 12 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
