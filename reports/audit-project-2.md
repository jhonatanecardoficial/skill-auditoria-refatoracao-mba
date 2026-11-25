================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack: Node.js + Express + SQLite
Files: 3 analyzed | ~180 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 2 | LOW: 2

## Findings

### [F1] [CRITICAL] Hardcoded Production Credentials e API Keys
File: src/utils.js:1-7
Description: Credenciais de banco de dados e chaves de API estão expostas diretamente no código-fonte (`dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `dbUser: "admin_master"`).
Impact: Exposição severa de credenciais de infraestrutura e gateways de pagamento no controle de versão, permitindo acesso indevido e movimentações financeiras não autorizadas.
Recommendation: Isolar todas as configurações sensíveis em variáveis de ambiente via `process.env` em `src/config/config.js`, garantindo carregamento seguro e ausência de segredos no código.

### [F2] [CRITICAL] Implementação Criptográfica Quebrada (Pseudo-Hash Inseguro)
File: src/utils.js:17-23, src/AppManager.js:68
Description: A função `badCrypto` itera 10.000 vezes concatenando partes de codificação Base64 e truncando a saída em apenas 10 caracteres (`hash.substring(0, 10)`), sem utilização de salt criptográfico ou algoritmo robusto.
Impact: As senhas dos usuários ficam extremamente vulneráveis a colisões, ataques de dicionário e engenharia reversa trivial, expondo a identidade de todos os alunos da plataforma.
Recommendation: Substituir por um algoritmo padrão da indústria com salt e derivação de chave robusta (ex.: `bcryptjs` ou `crypto.pbkdf2Sync`/`crypto.scryptSync`).

### [F3] [CRITICAL] Vazamento de Dados Sensíveis de Cartão nos Logs
File: src/AppManager.js:45
Description: A rota de checkout imprime no console os dados completos do cartão de crédito do cliente em conjunto com a chave de produção (`console.log("Processando cartão " + cc + " na chave " + config.paymentGatewayKey)`).
Impact: Violação direta de normas regulatórias de proteção a dados de pagamento (PCI-DSS) e leis de privacidade (LGPD/GDPR), tornando os números de cartão legíveis por qualquer processo ou operador com acesso aos logs de stdout.
Recommendation: Mascarar o número do cartão (mantendo apenas os 4 últimos dígitos) e suprimir totalmente a impressão de chaves privadas em logs de execução.

### [F4] [HIGH] God Class / Violação de Responsabilidade Única (SRP)
File: src/AppManager.js:1-139
Description: A classe `AppManager` acumula responsabilidades de inicialização do SQLite em memória, criação de schemas DDL, inserção de dados semente (seed), registro de rotas HTTP no Express, lógica de checkout, transações de pagamento e agregações para relatórios administrativos.
Impact: Acoplamento extremo entre persistência, regras de negócio e camada HTTP, tornando testes unitários inviáveis e manutenção propensa a efeitos colaterais severos.
Recommendation: Decompor o monolito na arquitetura MVC: rotas em `src/routes/`, lógica de negócio em `src/controllers/`, queries de persistência em `src/models/`, e inicialização da base de dados em `src/database/`.

### [F5] [HIGH] Callback Hell e Ausência de Controle de Fluxo Assíncrono
File: src/AppManager.js:37-77
Description: O fluxo do endpoint `/api/checkout` possui 5 níveis de callbacks aninhados para validar curso, verificar usuário, criar usuário, criar matrícula, registrar pagamento e salvar log de auditoria, além de controle manual de concorrência com contadores em relatórios.
Impact: Dificuldade extrema de leitura, manutenção e rastreamento de exceções; qualquer falha em um nível intermediário corre o risco de deixar operações pendentes ou travar respostas HTTP.
Recommendation: Refatorar o acesso assíncrono para Promises com `async/await`, estruturando operações atômicas e blocos claros de tratamento de erros.

### [F6] [HIGH] N+1 Query Problem no Relatório Financeiro
File: src/AppManager.js:89-125
Description: O endpoint `/api/admin/financial-report` busca todos os cursos com `SELECT * FROM courses`. Para cada curso retornado, executa uma busca por matrículas, e para cada matrícula executa consultas adicionais individuais para buscar usuário (`SELECT name, email FROM users WHERE id = ?`) e pagamento (`SELECT amount, status FROM payments WHERE enrollment_id = ?`).
Impact: Para $C$ cursos e $E$ matrículas, o servidor dispara $1 + C + 2 \times (C \times E)$ consultas ao banco de dados, degradando o tempo de resposta e gerando saturação desnecessária de I/O.
Recommendation: Substituir os loops aninhados de consultas por uma única query SQL relacional utilizando `LEFT JOIN` e funções de agregação (`SUM`, `COUNT`), ou consultas em lote com mapeamento eficiente em memória.

### [F7] [MEDIUM] Exclusão Inconsistente de Usuário com Registros Órfãos
File: src/AppManager.js:131-136
Description: O endpoint `/api/users/:id` executa a exclusão de um registro na tabela `users` sem verificar ou remover os registros dependentes nas tabelas `enrollments` e `payments`, deixando dados órfãos persistidos.
Impact: Corrupção da integridade referencial dos dados, podendo provocar falhas nas agregações financeiras e relatórios analíticos futuros.
Recommendation: Ativar verificação de chaves estrangeiras (`PRAGMA foreign_keys = ON;`) no SQLite e implementar deleção consistente em transação ou soft-delete para auditoria.

### [F8] [MEDIUM] Estado Mutável Global Compartilhado em Memória
File: src/utils.js:9-10, src/utils.js:12-15, src/AppManager.js:59
Description: As variáveis `globalCache` e `totalRevenue` são exportadas como objetos globais em memória e manipuladas por múltiplas rotas sem mecanismo de concorrência, controle de concorrência transacional ou limite de expiração (TTL).
Impact: Potencial vazamento de memória (Memory Leak) em servidores de longa duração e perda total de integridade dos dados durante reinicializações da aplicação.
Recommendation: Encapsular o gerenciamento de cache ou persistir totalizações e estados diretamente na base de dados relacional.

### [F9] [LOW] Parâmetros de Requisição Não Semânticos e Falta de Validação
File: src/AppManager.js:29-35
Description: Os parâmetros do payload do checkout utilizam abreviações obscuras (`usr`, `eml`, `pwd`, `c_id`, `card`) sem documentação ou validação tipada de entrada.
Impact: Dificuldade de compreensão do contrato por novos desenvolvedores e risco de aceitação de payloads defeituosos.
Recommendation: Adicionar camada de validação e sanitização dos dados de entrada, preservando compatibilidade com os campos existentes e documentando a API.

### [F10] [LOW] Tratamento de Erros Inconsistente e Ausência de Middleware Centralizado
File: src/AppManager.js:41, 51, 55, 70, 84
Description: Os erros nas operações de banco de dados são tratados de forma dispersa com retornos de strings cruas (`"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`) sem logging estruturado e sem retorno padrão em JSON.
Impact: Impossibilita o cliente da API de processar respostas de erro estruturadas e dificulta a observabilidade de falhas no ambiente produtivo.
Recommendation: Criar um middleware centralizado de tratamento de erros no Express que padronize a resposta com status HTTP e payload JSON (`{ error: ... }`).

================================
Total: 10 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
