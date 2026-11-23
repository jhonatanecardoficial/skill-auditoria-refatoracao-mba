================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack: Python 3 + Flask + SQLAlchemy
Files: 8 analyzed | ~700 lines of code

## Summary
CRITICAL: 3 | HIGH: 2 | MEDIUM: 1 | LOW: 2

## Findings

### [CRITICAL] Criptografia de Senhas Insegura com MD5
File: models/user.py:27-32
Description: O método `set_password` e a verificação `check_password` utilizam a função de dispersão MD5 pura sem aplicação de salt (`hashlib.md5(pwd.encode()).hexdigest()`), um algoritmo obsoleto e vulnerável a colisões imediatas e tabelas rainbow.
Impact: Caso o banco de dados seja vazado ou lido indevidamente, todas as senhas dos usuários podem ser descobertas instantaneamente, comprometendo completamente a segurança das contas.
Recommendation: Substituir o hashing MD5 por algoritmos modernos com derivação e salt integrado, como `werkzeug.security.generate_password_hash` e `check_password_hash` (PBKDF2/scrypt).

### [CRITICAL] Exposição de Senhas nas Respostas da API
File: models/user.py:16-25, routes/user_routes.py:33
Description: O método de serialização `to_dict()` da classe `User` expõe explicitamente o atributo `'password': self.password` no JSON retornado nas respostas de detalhamento e listagem de usuários.
Impact: Qualquer cliente que consuma as rotas de usuário recebe os hashes de senha das contas, violando princípios elementares de segurança e privacidade.
Recommendation: Remover permanentemente o campo `password` do dicionário retornado pelo método `to_dict()`, garantindo que credenciais nunca trafeguem nas respostas HTTP.

### [CRITICAL] Hardcoded Secret Key no Código-Fonte
File: app.py:13
Description: A configuração de chave secreta da aplicação está gravada diretamente no código: `app.config['SECRET_KEY'] = 'super-secret-key-123'`.
Impact: Permite que atacantes que tenham acesso ao repositório público forjem assinaturas de sessão, tokens criptografados e cookies de autenticação da aplicação.
Recommendation: Carregar a `SECRET_KEY` exclusivamente a partir de variáveis de ambiente (`os.getenv('SECRET_KEY')`), fornecendo um valor padrão dinâmico ou randômico apenas para ambiente de testes.

### [HIGH] N+1 Query Problem em Listagens e Relatórios
File: routes/task_routes.py:41-58, routes/report_routes.py:53-68, routes/user_routes.py:13-24
Description: Ao listar tarefas (`GET /tasks`), para cada tarefa iterada o código executa duas novas consultas ao banco de dados: `User.query.get(t.user_id)` e `Category.query.get(t.category_id)`. No relatório consolidado (`GET /reports/summary`), para cada usuário cadastrado é disparada uma busca separada por todas as suas tarefas (`Task.query.filter_by(user_id=u.id).all()`).
Impact: Causa explosão de queries ($1 + 2N$ ou $1 + N$), provocando latência excessiva, saturação de I/O e gargalo de escalabilidade na base SQLite.
Recommendation: Empregar carregamento ansioso (*eager loading*) utilizando `joinedload` do SQLAlchemy nas consultas ou agregar os dados diretamente na consulta SQL via `GROUP BY`.

### [HIGH] Fat Routes e Violação de Separação de Responsabilidades (MVC)
File: routes/task_routes.py:86-154, routes/report_routes.py:13-101
Description: Os arquivos de rotas contêm lógica de negócio pesada, manipulação manual de sessões do ORM (`db.session.add`, `db.session.commit`), regras de validação de dados em cascata e cálculos manuais de métricas de relatórios.
Impact: Alto acoplamento entre a camada HTTP e o banco de dados; impossibilidade de testar a lógica de negócios sem simular requisições HTTP e duplicação de regras em diferentes endpoints.
Recommendation: Isolar a lógica de negócio e orquestração de transações em camadas de serviço/controlador (`services/` ou `controllers/`), mantendo as rotas apenas como pontos de entrada e mapeamento de status HTTP.

### [MEDIUM] Captura Genérica e Mascaramento de Exceções (Bare Except)
File: routes/task_routes.py:62-63, 137-138, 236-238
Description: Utilização frequente de blocos `except:` sem especificar a classe de exceção tratada, engolindo erros com retornos genéricos de erro 500 sem registrar stack traces ou logs de diagnóstico.
Impact: Silencia falhas críticas de infraestrutura, `KeyboardInterrupt`, `MemoryError` ou erros de sintaxe e digitação, dificultando drasticamente a depuração de incidentes em ambiente produtivo.
Recommendation: Capturar classes de exceção específicas (`ValueError`, `SQLAlchemyError`) e registrar logs com `logging`, além de usar manipuladores centralizados de erro (`@app.errorhandler`).

### [LOW] Métodos e Funções Obsoletas e Depreciadas
File: models/user.py:14, models/task.py:15-16, routes/task_routes.py:42, 51, 67, 117, 122
Description: Utilização de `datetime.utcnow()` (depreciada a partir do Python 3.12 por não carregar timezone explícito) e de `Model.query.get(id)` (depreciada na versão 2.0 do SQLAlchemy).
Impact: Gera emissão de avisos `DeprecationWarning` no runtime e risco iminente de quebra de compatibilidade em atualizações futuras das bibliotecas.
Recommendation: Migrar para `datetime.now(timezone.utc)` e utilizar o padrão moderno `db.session.get(Model, id)`.

### [LOW] Lógica Booleana Redundante e Código Prolixo
File: models/user.py:34-38, models/task.py:38-48, 50-60
Description: Métodos de verificação como `is_admin`, `validate_status` e `is_overdue` utilizam condicionais `if ... return True else return False` em cascata em vez de retornar a expressão lógica diretamente.
Impact: Complexidade ciclomática desnecessária, piorando a legibilidade e manutenibilidade do código.
Recommendation: Simplificar os métodos retornando diretamente a expressão de comparação booleana (ex.: `return self.role == 'admin'`).

================================
Total: 8 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
