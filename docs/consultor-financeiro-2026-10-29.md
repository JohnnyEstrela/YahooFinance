# Consultor Financeiro — histórico e cálculos

Documento gerado a 2026-10-29 a partir da rotina diária "⚡ Consultor Financeiro".

## Pedido original
Rotina diária em que o utilizador adiciona empresas do portefólio ou a seguir, com dados relevantes e notícias de mercado, num design adaptável. Indicadores pedidos:

| Indicador | Barato / Desconto | Fair | Caro | Muito caro / Premium |
|---|---|---|---|---|
| P/E últimos 12 meses | < 15 | < 30 (pedido: ~20) | < 50 (pedido: ~40) | ≥ 50 |
| P/E próximos 12 meses | < 15 | < 30 | < 50 | ≥ 50 |
| PEG | < 1 | 1–2 | — | > 2 (Premium) |

Nota: o painel usa os cortes 15 / 30 / 50 para o P/E; o pedido original indicava 20 (fair) e 40 (caro). Convém confirmar qual preferes.

## Fórmulas usadas
- P/E 12m = preço ÷ EPS dos últimos 12 meses (só se EPS > 0).
- P/E próximos 12m = preço ÷ EPS estimado dos próximos 12 meses (só se > 0).
- Crescimento (%) = (EPS próximos 12m ÷ EPS 12m − 1) × 100.
- PEG = P/E próximos 12m ÷ crescimento (%). Não calculado se o lucro previsto desce ou não há lucro.
- Exemplo META: 19,94 ÷ 19,2 = 1,04. Exemplo AVGO: 18,77 ÷ 115,7 = 0,16.

## O que se fez em 2026-10-29
1. Leitura do painel existente (https://claude.ai/artifact/Ccwz65bhmktPXrTmYWinyD, 60 ações dos EUA + 5 europeias).
2. Preços e variações do dia via Wisesheets (FMP e Alpha Vantage bloqueiam cotações em lote por plano).
3. Recalculo de P/E e PEG com o preço de hoje, mantendo EPS e estimativas anteriores.
4. Notícias de mercado e por empresa via Bigdata.com; painel republicado.

Limitações: EPS 12m e estimativas não foram atualizados (o P/E da Alphabet fica subestimado após o falhanço do Q3). D2G, BAYN, M09, YSON e EDW mantêm preços de 13/10.

## Notícias de mercado
- **Macro e Fed** (alto): [Fed mantém taxas em 3,75%-4,00% (10-2, dois votos por subida); subida em dezembro com ~80% de probabilidade](https://app.bigdata.com/documents/B90A1F295EA98DD84456B852A0FBBB9E?cnum=2) — Benzinga, 2026-10-29. Yield a 10 anos ~5,0% e a 30 anos 5,33%. PIB do 3.º trim. +3,4% e PCE a 3,6% homólogo.
- **Macro e Fed** (medio): [Yield a 10 anos acima de 5% após PIB forte e inflação a acelerar](https://app.bigdata.com/documents/E5D92E2070147706798DFA81FCE6A432?cnum=1) — CNBC, 2026-10-29. Foco muda para o BCE.
- **Mercado de ações** (alto): [Alphabet tem o pior dia da sua história (−13%, ~510 mM$ de valor); Nasdaq −1,7% na abertura](https://app.bigdata.com/documents/C42445116498395E7162B5209BA25C3B?cnum=1) — Benzinga, 2026-10-29. S&P 500 −0,5% (~7.707). Comunicações −6,8%; saúde +2,7%. Dúvidas sobre o retorno do investimento em IA.
- **Tecnologia e chips** (alto): [Marvell −12% por possível compra da Lumentum (~83 mM$); acordo pode vir na próxima semana](https://app.bigdata.com/documents/FF3116A1DCA1C914FFAA8692E94D9BA2?cnum=1) — Yahoo! Finance, 2026-10-29. Receio de diluição e financiamento. Lumentum sobe 2-5%.
- **Tecnologia e chips** (medio): [Intel e Amazon reportam hoje após o fecho; semicondutores em queda (Nvidia −1%, AMD −3%)](https://app.bigdata.com/documents/BB4B062BA0D91FF7C51F61212EE03121?cnum=3) — Reuters / AOL, 2026-10-29. ServiceNow −19%; Caterpillar −9,7% apesar de lucros fortes.
- **Energia e geopolítica** (alto): [Petróleo recua: Brent ~113-114 $, WTI ~100-102 $ com Vance a tentar relançar negociações com o Irão](https://app.bigdata.com/documents/A3E9A010C5938469F96EF3CB276307E2?cnum=1) — CNBC, 2026-10-29. Trump pondera novos ataques após as intercalares de 3 de novembro. Brent estava a ~72 $ antes da guerra.

## Tabela completa
| Ticker | Nome | Preço | Var. dia | EPS 12m | EPS próx. 12m | P/E 12m | P/E próx. 12m | PEG |
|---|---|---|---|---|---|---|---|---|
| AVGO | Broadcom Inc. | 343.08 USD | -2.48% | 8.06 | 17.39 | 42.56 (Caro) | 19.73 (Fair) | 0.17 (Desconto) |
| META | Meta Platforms Inc. | 625.36 USD | 2.10% | 26.82 | 31.97 | 23.32 (Fair) | 19.56 (Fair) | 1.02 (Fair) |
| MU | Micron Technology Inc. | 952.68 USD | -3.11% | 76.68 | 173.94 | 12.42 (Barato) | 5.48 (Barato) | 0.04 (Desconto) |
| VST | Vistra Corp. | 143.45 USD | 0.51% | 5.99 | 10.27 | 23.95 (Fair) | 13.97 (Barato) | 0.20 (Desconto) |
| SOFI | SoFi Technologies Inc. | 17.46 USD | 1.90% | 0.51 | 0.78 | 34.25 (Caro) | 22.50 (Fair) | 0.43 (Desconto) |
| UBER | Uber Technologies Inc. | 65.22 USD | -0.07% | 4.62 | 4.13 | 14.12 (Barato) | 15.79 (Fair) | — (n/d) |
| PGY | Pagaya Technologies Ltd. | 20.89 USD | 2.05% | 1.50 | 2.15 | 13.93 (Barato) | 9.71 (Barato) | 0.22 (Desconto) |
| RKLB | Rocket Lab Corp. | 59.93 USD | 2.27% | -0.20 | — | — (n/d) | — (n/d) | — (n/d) |
| D2G | Ørsted A/S | 19.69 USD | -1.54% | -5.27 | — | — (n/d) | 13.54 (Barato) | — (n/d) |
| SRFM | Surf Air Mobility Inc. | 0.80 USD | 2.55% | -2.01 | — | — (n/d) | — (n/d) | — (n/d) |
| ONDS | Ondas Inc. | 6.96 USD | 1.46% | -0.65 | — | — (n/d) | — (n/d) | — (n/d) |
| XE | X-Energy Inc. | 11.59 USD | 0.43% | -0.75 | — | — (n/d) | — (n/d) | — (n/d) |
| QNT | Quantinuum Inc. | 37.68 USD | -1.70% | -1.56 | — | — (n/d) | — (n/d) | — (n/d) |
| COSM | Cosmos Health Inc. | 0.27 USD | 6.79% | -0.74 | — | — (n/d) | — (n/d) | — (n/d) |
| GENB | Generate Biomedicines Inc. | 15.93 USD | 3.60% | -2.44 | — | — (n/d) | — (n/d) | — (n/d) |
| NEO | NeoGenomics Inc. | 17.08 USD | -5.06% | 0.13 | 0.31 | 131.38 (Muito caro) | 55.26 (Muito caro) | 0.40 (Desconto) |
| NVDA | NVIDIA Corp. | 214.10 USD | -0.59% | 5.84 | 13.92 | 36.66 (Caro) | 15.38 (Fair) | 0.11 (Desconto) |
| XYL | Xylem Inc. | 89.20 USD | 1.10% | 5.17 | 5.99 | 17.25 (Fair) | 14.88 (Barato) | 0.93 (Desconto) |
| AGBK | AGBK | 5.16 USD | 1.18% | 0.59 | — | 8.75 (Barato) | — (n/d) | — (n/d) |
| BN | Brookfield Corp. | 39.35 USD | 2.23% | 2.76 | 3.29 | 14.25 (Barato) | 11.95 (Barato) | 0.62 (Desconto) |
| MA | Mastercard Inc. | 638.64 USD | 4.64% | 17.89 | 22.15 | 35.70 (Caro) | 28.84 (Fair) | 1.21 (Fair) |
| AMZN | Amazon.com Inc. | 247.47 USD | -2.80% | 12.43 | 11.11 | 19.91 (Fair) | 22.28 (Fair) | — (n/d) |
| CSCO | Cisco Systems Inc. | 109.43 USD | -0.78% | 4.09 | 5.20 | 26.75 (Fair) | 21.05 (Fair) | 0.78 (Desconto) |
| GRAB | Grab Holdings Ltd. | 2.75 USD | 0.00% | 0.14 | 0.19 | 19.84 (Fair) | 14.56 (Barato) | 0.40 (Desconto) |
| GLW | Corning Inc. | 131.32 USD | 0.10% | 2.69 | 3.98 | 48.82 (Caro) | 32.97 (Caro) | 0.69 (Desconto) |
| LULU | Lululemon Athletica Inc. | 108.23 USD | 2.86% | 12.40 | 8.22 | 8.73 (Barato) | 13.16 (Barato) | — (n/d) |
| NKE | Nike Inc. | 38.19 USD | 2.80% | 2.09 | 1.37 | 18.27 (Fair) | 27.96 (Fair) | — (n/d) |
| MCD | McDonald's Corp. | 254.69 USD | 1.67% | 12.55 | 13.47 | 20.29 (Fair) | 18.91 (Fair) | 2.59 (Premium) |
| LITE | Lumentum Holdings Inc. | 936.92 USD | 2.51% | 6.02 | 24.96 | 155.64 (Muito caro) | 37.54 (Caro) | 0.12 (Desconto) |
| AAOI | Applied Optoelectronics Inc. | 81.25 USD | -1.18% | -0.33 | 3.59 | — (n/d) | 22.61 (Fair) | — (n/d) |
| AEHR | Aehr Test Systems | 62.92 USD | -2.51% | 0.03 | 0.86 | 2,097.33 (Muito caro) | 73.33 (Muito caro) | 0.03 (Desconto) |
| NVO | Novo Nordisk A/S | 38.82 USD | 1.38% | 4.02 | 3.31 | 9.66 (Barato) | 11.74 (Barato) | — (n/d) |
| CRCL | Circle Internet Group | 80.06 USD | -2.02% | 1.46 | — | 54.84 (Muito caro) | — (n/d) | — (n/d) |
| IBM | IBM Corp. | 253.10 USD | -0.05% | 11.88 | 12.92 | 21.31 (Fair) | 19.59 (Fair) | 2.23 (Premium) |
| AMPX | Amprius Technologies | 9.19 USD | 0.33% | -0.11 | 0.03 | — (n/d) | 309.43 (Muito caro) | — (n/d) |
| NNE | Nano Nuclear Energy | 12.39 USD | 0.00% | -0.69 | — | — (n/d) | — (n/d) | — (n/d) |
| BR | Broadridge Financial Solutions | 177.50 USD | 0.30% | 9.64 | 10.80 | 18.41 (Fair) | 16.43 (Fair) | 1.36 (Fair) |
| GOOGL | Alphabet Inc. | 285.65 USD | -12.08% | 19.91 | 16.38 | 14.35 (Barato) | 17.44 (Fair) | — (n/d) |
| SYM | Symbotic Inc. | 38.92 USD | -0.13% | 0.83 | 0.42 | 46.88 (Caro) | 92.66 (Muito caro) | — (n/d) |
| TER | Teradyne Inc. | 297.16 USD | -5.13% | 7.68 | 10.87 | 38.70 (Caro) | 27.33 (Fair) | 0.66 (Desconto) |
| IONQ | IonQ Inc. | 32.00 USD | -1.32% | -4.66 | — | — (n/d) | — (n/d) | — (n/d) |
| VIAV | Viavi Solutions Inc. | 33.87 USD | -1.71% | 0.98 | 1.67 | 34.56 (Caro) | 20.29 (Fair) | 0.29 (Desconto) |
| SHOP | Shopify Inc. | 167.41 USD | -0.48% | 1.58 | 2.19 | 105.95 (Muito caro) | 76.31 (Muito caro) | 1.96 (Fair) |
| INTC | Intel Corp. | 92.66 USD | -3.00% | 0.57 | 1.90 | 162.56 (Muito caro) | 48.72 (Caro) | 0.21 (Desconto) |
| PANW | Palo Alto Networks | 379.02 USD | -3.92% | 3.76 | 4.19 | 100.80 (Muito caro) | 90.52 (Muito caro) | 7.97 (Premium) |
| CBRS | Cerebras Systems | 118.09 USD | 4.91% | -0.04 | 0.26 | — (n/d) | 452.97 (Muito caro) | — (n/d) |
| NEE | NextEra Energy | 82.19 USD | 1.44% | 3.80 | 4.18 | 21.62 (Fair) | 19.65 (Fair) | 1.95 (Fair) |
| PLTR | Palantir Technologies | 195.55 USD | -0.64% | 1.20 | 2.09 | 162.95 (Muito caro) | 93.63 (Muito caro) | 1.26 (Fair) |
| INDI | indie Semiconductor | 1.76 USD | 0.41% | -0.28 | — | — (n/d) | — (n/d) | — (n/d) |
| SPGI | S&P Global Inc. | 457.31 USD | 1.78% | 18.16 | 19.55 | 25.19 (Fair) | 23.39 (Fair) | 3.05 (Premium) |
| MCO | Moody's Corp. | 485.40 USD | 1.70% | 16.57 | 18.34 | 29.29 (Fair) | 26.47 (Fair) | 2.48 (Premium) |
| MRVL | Marvell Technology | 219.60 USD | -12.73% | 3.30 | 5.66 | 66.54 (Muito caro) | 38.80 (Caro) | 0.54 (Desconto) |
| BE | Bloom Energy | 227.58 USD | -0.22% | 1.14 | 4.40 | 199.63 (Muito caro) | 51.75 (Muito caro) | 0.18 (Desconto) |
| VRT | Vertiv Holdings | 250.75 USD | 3.21% | 4.72 | 8.63 | 53.12 (Muito caro) | 29.06 (Fair) | 0.35 (Desconto) |
| EME | EMCOR Group | 718.29 USD | 5.86% | 29.67 | 35.73 | 24.21 (Fair) | 20.10 (Fair) | 0.98 (Desconto) |
| CRWV | CoreWeave Inc. | 62.66 USD | -1.99% | -2.02 | — | — (n/d) | — (n/d) | — (n/d) |
| LEU | Centrus Energy Corp. | 112.49 USD | 0.46% | 2.20 | 2.50 | 51.13 (Muito caro) | 44.96 (Caro) | 3.27 (Premium) |
| BAYN | Bayer AG | 49.45 USD | 0.73% | -1.76 | 4.49 | — (n/d) | 9.83 (Barato) | — (n/d) |
| M09 | Mota-Engil SGPS | 5.31 USD | 1.15% | — | — | — (n/d) | — (n/d) | — (n/d) |
| YSON | Sonae SGPS | 2.30 USD | 0.24% | 0.12 | — | 18.45 (Fair) | — (n/d) | — (n/d) |
| EDW | EDP Renováveis | 14.08 USD | 0.88% | 0.32 | — | 43.43 (Caro) | — (n/d) | — (n/d) |
| JNJ | Johnson & Johnson | 275.04 USD | 1.47% | 10.73 | 11.91 | 25.63 (Fair) | 23.10 (Fair) | 2.10 (Premium) |
| VNOM | Viper Energy | 46.74 USD | 0.60% | 2.02 | 2.71 | 23.14 (Fair) | 17.22 (Fair) | 0.50 (Desconto) |
| ACHR | Archer Aviation | 4.42 USD | 1.84% | -1.08 | — | — (n/d) | — (n/d) | — (n/d) |
| ASML | ASML Holding | 1,675.34 USD | 0.75% | 32.02 | 52.99 | 52.33 (Muito caro) | 31.61 (Caro) | 0.48 (Desconto) |

Apoio à decisão, não é aconselhamento financeiro.
