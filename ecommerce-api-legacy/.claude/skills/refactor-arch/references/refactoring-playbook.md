# Playbook de Refatoração Arquitetural e Transformações

Este documento orienta a **Fase 3 (Refatoração)** da skill `refactor-arch`, fornecendo padrões concretos de transformação com exemplos de código **Antes / Depois** cobrindo Python e Node.js.

---

## Padrão 1: Eliminação de SQL Injection (Consultas Parametrizadas)

### Antes (Python / SQLite Inseguro):
```python
# Inseguro: vulnerável a injeção SQL via concatenação
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES ('" + nome + "', '" + email + "')")
```

### Depois (Python / Parametrizado):
```python
# Seguro: utiliza placeholders e tupla de parâmetros
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES (?, ?)", (nome, email))
```

---

## Padrão 2: Decomposição de God Class / God Module em Camadas MVC

### Antes (Node.js / Monólito em `AppManager.js`):
```javascript
// AppManager.js centralizando conexão, tabelas, rotas e regras
class AppManager {
  initDb() { this.db.run("CREATE TABLE ..."); }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => {
      this.db.get("SELECT ...", (err, course) => {
        this.db.run("INSERT ...", (err) => { res.send("OK"); });
      });
    });
  }
}
```

### Depois (Node.js / MVC Separado):
```javascript
// models/course.model.js
class CourseModel {
  static async findById(db, id) {
    return new Promise((resolve, reject) => {
      db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [id], (err, row) => err ? reject(err) : resolve(row));
    });
  }
}

// controllers/checkout.controller.js
class CheckoutController {
  constructor(checkoutService) { this.service = checkoutService; }
  async handle(req, res, next) {
    try {
      const result = await this.service.execute(req.body);
      return res.status(200).json(result);
    } catch (err) { next(err); }
  }
}

// routes/checkout.routes.js
const router = express.Router();
router.post('/checkout', (req, res, next) => checkoutController.handle(req, res, next));
```

---

## Padrão 3: Externalização de Configurações e Segredos

### Antes (Hardcoded no arquivo de aplicação):
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

### Depois (Isolado em `config/settings.py` via variáveis de ambiente):
```python
# config/settings.py
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-key-only")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")

# app.py
from config.settings import Config
app.config.from_object(Config)
```

---

## Padrão 4: Criptografia Forte e Proteção de Dados Sensíveis

### Antes (Inseguro: MD5 sem salt e vazamento de senha no retorno):
```python
# models.py
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def to_dict(self):
    return {'id': self.id, 'name': self.name, 'password': self.password}
```

### Depois (Seguro: Werkzeug / bcrypt e omissão de credencial):
```python
# models.py
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)

def to_dict(self):
    # Nunca retorna a senha ou seu hash
    return {'id': self.id, 'name': self.name, 'email': self.email, 'role': self.role}
```

---

## Padrão 5: Desacoplamento de Regras de Negócio dos Controllers

### Antes (Lógica de pedido e notificações no controller):
```python
# controllers.py
def criar_pedido():
    # Loop de cálculo, alteração de estoque e prints manuais de SMS/Email
    for item in itens: ...
    print("ENVIANDO EMAIL...")
    print("ENVIANDO SMS...")
```

### Depois (Serviço de Domínio orquestrado):
```python
# services/pedido_service.py
class PedidoService:
    def __init__(self, pedido_repo, produto_repo, notification_service):
        self.pedido_repo = pedido_repo
        self.produto_repo = produto_repo
        self.notifier = notification_service

    def criar_pedido(self, usuario_id, itens):
        # Validação de regras e estoque
        total = self.calcular_total(itens)
        pedido = self.pedido_repo.salvar(usuario_id, itens, total)
        self.notifier.notificar_criacao(pedido)
        return pedido
```

---

## Padrão 6: Eliminação de Callback Hell (Promises / Async Await)

### Antes (Node.js Callback Pyramid):
```javascript
// AppManager.js
db.get(query1, [p1], (err, res1) => {
  db.get(query2, [p2], (err, res2) => {
    db.run(query3, [p3], function(err) {
      db.run(query4, [p4], function(err) {
        res.send("OK");
      });
    });
  });
});
```

### Depois (Promisificação limpa com Async/Await):
```javascript
// services/checkout.service.js
async function processCheckout(payload) {
  const course = await dbGet(query1, [payload.c_id]);
  const user = await dbGet(query2, [payload.eml]);
  const enrollmentId = await dbRun(query3, [user.id, course.id]);
  await dbRun(query4, [enrollmentId, course.price]);
  return { success: true, enrollmentId };
}
```

---

## Padrão 7: Resolução do Anti-Pattern N+1 Query

### Antes (Execução de query por item em loop):
```python
# models.py
pedidos = cursor.execute("SELECT * FROM pedidos").fetchall()
for p in pedidos:
    # N queries adicionais disparadas
    itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (p['id'],)).fetchall()
```

### Depois (JOIN único com agregação):
```python
# models.py
cursor.execute("""
    SELECT p.id, p.total, p.status, ip.produto_id, pr.nome as produto_nome, ip.quantidade, ip.preco_unitario
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
""")
rows = cursor.fetchall()
# Agrupamento estruturado em memória O(N)
```

---

## Padrão 8: Modernização de APIs Deprecated

### Caso A: `datetime.utcnow()` no Python 3.12+
```python
# Antes (Deprecated):
from datetime import datetime
created_at = datetime.utcnow()

# Depois (Canônico e compatível):
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

### Caso B: `Model.query.get(id)` no SQLAlchemy 2.0+
```python
# Antes (Padrão legado SQLAlchemy 1.x):
user = User.query.get(user_id)

# Depois (Padrão SQLAlchemy 2.0 com session):
user = db.session.get(User, user_id)
```

---

## Padrão 9: Tratamento Centralizado de Erros e Remoção de Bare Except

### Antes (Bare except silencioso):
```python
try:
    process_data()
except:
    return jsonify({'error': 'Erro interno'}), 500
```

### Depois (Middleware global e exceções tipadas):
```python
# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def handle_validation_error(exc):
        return jsonify({'error': str(exc), 'status': 'fail'}), 400

    @app.errorhandler(Exception)
    def handle_generic_error(exc):
        app.logger.error(f"Erro inesperado: {exc}")
        return jsonify({'error': 'Erro interno do servidor', 'status': 'error'}), 500
```

---

## Padrão 10: Substituição de Magic Numbers e Nomes Crípticos

### Antes:
```javascript
let u = req.body.usr;
let cc = req.body.card;
if (cc.startsWith("4")) { ... }
```

### Depois:
```javascript
const { userName, cardNumber } = req.body;
const VISA_PREFIX = "4";
const isPaymentApproved = cardNumber.startsWith(VISA_PREFIX);
```
