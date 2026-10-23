# Consultor Financeiro

1. Edita `carteira.json` (tipo `carteira` ou `seguir`; quantidade/preço médio opcionais).
2. `pip install yfinance && python relatorio.py`
3. Abre `relatorio.html` (responsivo, claro/escuro, filtros e ordenação).

Mostra P/E (12m passados), P/E (próx. 12m) e PEG com classificação segundo os `limiares` do JSON, mais notícias por empresa e do mercado.
Se o Yahoo não fornecer PEG, é estimado como P/E forward ÷ crescimento de lucros.
