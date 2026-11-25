# Template de Relatório de Auditoria Arquitetural (Fase 2)

Este documento define o formato padronizado e obrigatório de saída para a **Fase 2 (Auditoria Arquitetural)** da skill `refactor-arch`.

---

## Estrutura do Relatório

O relatório deve seguir rigorosamente a seguinte estrutura em texto/Markdown:

```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack: <Linguagem + Framework>
Files: <N> analyzed | ~<X> lines of code

## Summary
CRITICAL: <count> | HIGH: <count> | MEDIUM: <count> | LOW: <count>

## Findings

### [<SEVERITY>] <Nome do Anti-Pattern>
File: <caminho/arquivo>:<linhas>
Description: <Descrição clara e contextualizada do problema encontrado>
Impact: <Impacto arquitetural, de segurança ou de manutenibilidade>
Recommendation: <Ação corretiva recomendada para a Fase 3>

[... repetir para cada finding identificado, ordenado por severidade: CRITICAL -> HIGH -> MEDIUM -> LOW ...]

================================
Total: <total_findings> findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Critérios de Validação do Relatório

1. **Ordenação por Severidade:** Os achados devem ser apresentados obrigatoriamente agrupados ou ordenados do mais grave para o menos grave: `CRITICAL` → `HIGH` → `MEDIUM` → `LOW`.
2. **Localização Exata:** Cada achado deve indicar o arquivo e intervalo ou linha específica (ex.: `models.py:28-50` ou `AppManager.js:45`).
3. **Consistência Aritmética Rigorosa:** O sumário executivo no início do relatório deve conter números estritamente consistentes:
   `CRITICAL: C | HIGH: H | MEDIUM: M | LOW: L` onde `C + H + M + L == Total`. A contagem descrita no sumário deve corresponder com precisão absoluta à quantidade de blocos de achados detalhados no corpo do relatório e no rodapé.
4. **Cotas Mínimas Exigidas:** O relatório de auditoria e a análise manual devem conter no mínimo:
   - Pelo menos 1 achado `CRITICAL` ou `HIGH`;
   - Pelo menos 2 achados `MEDIUM`;
   - Pelo menos 2 achados `LOW`.
5. **Pausa para Confirmação Humana:** Ao final da emissão do relatório, a skill deve **pausar obrigatoriamente** exibindo a pergunta `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`, aguardando a aprovação explícita do usuário antes de realizar qualquer alteração na codebase.
