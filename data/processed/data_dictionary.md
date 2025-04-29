# Dicionário de Dados — Rebanho Bovino Brasil

## Fonte: Dataset Consolidado (dataset_consolidado.csv)

| Coluna | Tipo | Descrição | Fonte |
|--------|------|-----------|-------|
| uf | str | Sigla da Unidade Federativa | IBGE |
| ano | int | Ano de referência (2004–2023) | — |
| rebanho_cabecas | int | Efetivo de bovinos (cabeças) | IBGE/PPM Tabela 3939 |
| regiao | str | Região geográfica (Norte, Nordeste, etc.) | Derivado |
| abate_anual | int | Total de bovinos abatidos no ano | IBGE/SIDRA Tabela 1092 |
| desmatamento_km2 | float | Área desmatada no ano (km²) — apenas Amazônia Legal | INPE/PRODES |
| taxa_abate | float | Abate/Rebanho × 100 (proxy de produtividade) | Derivado |
| amazonia_legal | bool | Se o estado pertence à Amazônia Legal | Derivado |
| var_rebanho_pct | float | Variação % do rebanho em relação ao ano anterior | Derivado |

## Notas
- Desmatamento está disponível apenas para 9 estados da Amazônia Legal
- Taxa de abate é utilizada como proxy de intensificação produtiva
- Dados de rebanho do IBGE via API SIDRA (ou estimativa calibrada quando API indisponível)
