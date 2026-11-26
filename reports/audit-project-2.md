================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack: Node.js + Express + SQLite
Files: 3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 2 | MEDIUM: 3 | LOW: 2

## Findings

### [F1] [CRITICAL] Hardcoded Production Credentials e API Keys
File: src/utils.js:1-7
Description: Credenciais de banco de dados e chaves de API estão expostas diretamente no código-fonte (`dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `dbUser: "admin_master"`).
Impact: Exposição severa de credenciais de infraestrutura e gateways de pagamento no controle de versão, permitindo acesso indevido e movimentações financeiras não autorizadas.
Recommendation: Isolar todas as configurações sensíveis em variáveis de ambiente via `process.env` em `src/config/config.js`, com comportamento fail-closed e sem fallbacks literais.

### [F2] [CRITICAL] Implementação Criptográfica Quebrada (Pseudo-Hash) e Senha Seed em Texto Claro
File: src/utils.js:17-23, src/AppManager.js:18, 68
Description: A função `badCrypto` itera 10.000 vezes concatenando partes de Base64 e truncando a saída em apenas 10 caracteres sem salt, enquanto o usuário seed inicial (`Leonan`) é inserido com senha `'123'` em texto puro.
Impact: Senhas extremamente vulneráveis a colisões, ataques de dicionário e comprometimento trivial das contas armazenadas.
Recommendation: Substituir por `crypto.pbkdf2Sync` com salt aleatório por senha, comparação em tempo constante (`crypto.timingSafeEqual`) e aplicar hashing também nos seeds.

### [F3] [CRITICAL] Vazamento de Dados Sensíveis de Cartão e Chave nos Logs (PCI-DSS)
File: src/AppManager.js:45
Description: A rota de checkout imprime no console o número completo do cartão de crédito do cliente em conjunto com a chave privada do gateway (`console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`).
Impact: Violação direta de normas regulatórias PCI-DSS e leis de privacidade (LGPD), expondo dados financeiros no stdout da aplicação.
Recommendation: Mascarar o cartão (preservando apenas os 4 últimos dígitos) e suprimir totalmente a impressão de chaves nos logs.

### [F4] [CRITICAL] Endpoint Administrativo de Relatório Financeiro Sem Autenticação
File: src/AppManager.js:80-129
Description: A rota administrativa `/api/admin/financial-report` é registrada diretamente no Express sem nenhum middleware de autenticação Bearer ou verificação de papel administrativo, expondo publicamente receitas por curso, nomes de alunos e pagamentos realizados.
Impact: Qualquer cliente anônimo na rede consegue extrair faturamento da empresa e dados financeiros/pessoais de todos os estudantes.
Recommendation: Proteger `GET /api/admin/financial-report` com middleware `requireAdmin` exigindo token Bearer assinado (HMAC-SHA256 com chave via CSPRNG/env) e revalidação de `role === 'admin'` no banco de dados.

### [F5] [CRITICAL] God Class / Violação Total de Responsabilidade Única (SRP)
File: src/AppManager.js:1-141
Description: A classe `AppManager` acumula inicialização do SQLite em memória, criação de schemas DDL, seeds, roteamento Express, regras de checkout, transações de pagamento e agregações para relatórios administrativos.
Impact: Acoplamento extremo entre persistência, transporte HTTP e regras de negócio, inviabilizando testes isolados e manutenção segura.
Recommendation: Decompor o monolito em camadas MVC: `src/config/`, `src/database/`, `src/models/`, `src/controllers/`, `src/routes/`, `src/services/` e `src/middlewares/`.

### [F6] [HIGH] Callback Hell e Ausência de Controle de Fluxo Assíncrono
File: src/AppManager.js:37-77, 89-128
Description: O fluxo de `/api/checkout` possui 5 níveis de callbacks aninhados e o relatório financeiro usa contadores manuais (`coursesPending`, `enrPending`) sujeitos a race conditions e travamento de resposta em caso de falha intermediária.
Impact: Código frágil, difícil de depurar e propenso a erros silenciosos ou respostas HTTP nunca finalizadas.
Recommendation: Promisificar o acesso ao SQLite (`dbGet`/`dbAll`/`dbRun`) e adotar `async/await` com tratamento estruturado de exceções.

### [F7] [HIGH] Estado Global Mutável Compartilhado em Memória
File: src/utils.js:9-15, src/AppManager.js:59
Description: As variáveis `globalCache = {}` e `totalRevenue = 0` são exportadas e mutadas globalmente sem limite de capacidade ou encapsulamento.
Impact: Vazamento progressivo de memória (*memory leak*) em servidores de longa duração e risco de inconsistência sob concorrência.
Recommendation: Encapsular o cache em uma estrutura limitada (`BoundedCache`) e calcular receitas diretamente a partir da base relacional.

### [F8] [MEDIUM] N+1 Query Problem no Relatório Financeiro
File: src/AppManager.js:89-125
Description: Para cada curso retornado, o endpoint dispara consultas em loop para matrículas e, dentro de cada matrícula, dispara queries individuais para usuário (`users`) e pagamento (`payments`).
Impact: Explosão de queries ($1 + C + 2 \times C \times E$), degradando severamente a performance com o crescimento da base.
Recommendation: Substituir os loops por consulta única com `LEFT JOIN` encapsulada em `ReportModel`.

### [F9] [MEDIUM] Exclusão Inconsistente de Usuário com Registros Órfãos
File: src/AppManager.js:131-136
Description: O endpoint `DELETE /api/users/:id` exclui apenas a linha na tabela `users`, sem chaves estrangeiras ativas e sem remover `enrollments` e `payments` dependentes.
Impact: Corrupção de integridade referencial gerando linhas órfãs e distorções permanentes no relatório financeiro.
Recommendation: Ativar `PRAGMA foreign_keys = ON;`, remover registros dependentes em lote no `UserModel` e impedir exclusão indevida de contas `admin`.

### [F10] [MEDIUM] Tratamento de Erros Descentralizado e Retornos em Texto Cru
File: src/AppManager.js:41, 51, 55, 70, 84
Description: Erros de banco são tratados de forma repetitiva devolvendo strings cruas (`"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`) sem padronização JSON nem middleware centralizado.
Impact: Dificulta consumo por clientes de API e prejudica a observabilidade de falhas internas.
Recommendation: Criar middleware centralizado `errorHandler` em JSON sem vazar detalhes internos em erros 500.

### [F11] [LOW] Nomenclatura Críptica de Variáveis e Parâmetros
File: src/AppManager.js:29-35
Description: Parâmetros e variáveis locais usam siglas obscuras de uma letra (`u`, `e`, `p`, `cid`, `cc`), reduzindo a legibilidade do fluxo de checkout.
Impact: Dificulta onboarding de desenvolvedores e revisão de código.
Recommendation: Adotar identificadores semânticos no código (`userName`, `email`, `rawPassword`, `courseId`, `cardNumber`) mantendo compatibilidade com o contrato JSON de entrada.

### [F12] [LOW] Magic Numbers e Literais Soltos no Código
File: src/AppManager.js:19, 46, 68, src/utils.js:19-22
Description: Literais como prefixo `"4"` de cartão VISA, `10000` iterações e truncamento `10` aparecem soltos sem constantes declaradas.
Impact: Reduz clareza das regras de negócio e dificulta manutenção.
Recommendation: Extrair constantes nomeadas (`VISA_CARD_PREFIX`, `MAX_CACHE_SIZE`).

================================
Total: 12 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
