# Relatório Comparativo de Risco Moderado (2,5% por Trade) — 360 Dias

**Protocolo de Referência:** [`Prompt2.md`](file:///c:/Users/bmani/Documents/GitHub/Bruno/Project/Prompt2.md)  
**Calibragem:** **Risco Fixo de 2,5% por Trade** ($\text{Alocação} = \frac{2,5\%}{\text{Distância do Stop}}$) com limite de **até 3 posições simultâneas** e taxas reais da Binance (0,075% BNB).

---

## 1. Tabela Comparativa dos Horizontes Temporais (Base R$ 100.000)

| Período Histórico | Capital Inicial | Saldo Final | Lucro Líquido (R$) | Retorno (%) | Drawdown Máximo | Profit Factor | Win Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. 360d a 180d (Ago/25 a Fev/26)** *(Fase do Crash)* | R$ 100.000,00 | **R$ 81.311,64** | -R$ 18.688,36 | **-18,69%** | **30,22%** | 0,72 | 27,27% |
| **2. 180d a 0d (Fev/26 a Ago/26)** *(Fase de Retomada)* | R$ 100.000,00 | **R$ 129.544,47** | **+R$ 29.544,47** | **+29,54%** | **12,38%** | **1,69** | 33,96% |
| **3. Total 360d Contínuo (1 Ano Completo)** | R$ 100.000,00 | **R$ 105.334,73** | **+R$ 5.334,73** | **+5,33%** | **30,33%** | **1,05** | 30,93% |

---

## 2. Comparativo Direto: Risco 5,0% (Agressivo) vs Risco 2,5% (Moderado)

| Cenário de Mercado | Risco 5,0% (Super Agressivo) | Risco 2,5% (Moderado / Recomendado) | Vantagem do Risco 2,5% |
| :--- | :---: | :---: | :--- |
| **No Crash de Altcoins (Ago/25 a Fev/26)** | -36,16% (DD: 50,89%) | **-18,69% (DD: 30,22%)** | **Preserva o dobro do capital nas crises** |
| **Na Retomada / Bull Market (Fev/26 a Ago/26)** | +63,14% (DD: 23,55%) | **+29,54% (DD: 12,38%)** | **Lucro expressivo com drawdown de apenas 12%** |
| **No Ano Completo (360 Dias Contínuos)** | +4,15% (DD: ~50%) | **+5,33% (DD: 30,33%)** | **Maior retorno final e menor volatilidade** |

---

## 3. Conclusão da Engenharia Quantitativa

O teste comprovou a **matemática da preservação de capital**:
* Com **Risco de 2,5%**, a perda durante o bear market é muito menor.
* Isso evita a "armadilha da descapitalização" (onde uma perda de -50% exige +100% só para voltar ao 0x0).
* Como resultado, **o retorno líquido em 1 ano completo foi SUPERIOR com Risco de 2,5% (+5,33% vs +4,15%)**, oferecendo um perfil de risco-retorno infinitamente mais confortável e seguro.
