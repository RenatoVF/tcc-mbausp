# Selecao estratificada para revisao humana (test_set)

Amostragem estratificada com seed fixa `20260832` (derivada da seed de geracao dos planos, `20260831`, documentada em `gerar_test_set.py`): 5 pares por nivel de complexidade, sendo em cada nivel 4 pares de violacao unica (sorteados entre as regras, priorizando cobertura) e 1 par de violacao multipla. Total: 15 pares (30 planos).

| Arquivo Compliant | Arquivo Non-compliant | Complexidade | Regra(s) | Tipo |
|---|---|---|---|---|
| compliant-simple-03-02 | noncompliant-simple-03-02 | simple | 03 | unica |
| compliant-simple-04a-05 | noncompliant-simple-04a-05 | simple | 04A | unica |
| compliant-simple-01-02 | noncompliant-simple-01-02 | simple | 01 | unica |
| compliant-simple-04b-02 | noncompliant-simple-04b-02 | simple | 04B | unica |
| compliant-simple-multi-05 | noncompliant-simple-multi-05 | simple | 02+03 | multipla |
| compliant-medium-03-01 | noncompliant-medium-03-01 | medium | 03 | unica |
| compliant-medium-01-02 | noncompliant-medium-01-02 | medium | 01 | unica |
| compliant-medium-02-04 | noncompliant-medium-02-04 | medium | 02 | unica |
| compliant-medium-04a-03 | noncompliant-medium-04a-03 | medium | 04A | unica |
| compliant-medium-multi-02 | noncompliant-medium-multi-02 | medium | 03+04B | multipla |
| compliant-complex-04a-01 | noncompliant-complex-04a-01 | complex | 04A | unica |
| compliant-complex-04b-05 | noncompliant-complex-04b-05 | complex | 04B | unica |
| compliant-complex-01-02 | noncompliant-complex-01-02 | complex | 01 | unica |
| compliant-complex-02-03 | noncompliant-complex-02-03 | complex | 02 | unica |
| compliant-complex-multi-05 | noncompliant-complex-multi-05 | complex | 03+04A | multipla |
