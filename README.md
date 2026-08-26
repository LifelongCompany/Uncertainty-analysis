# Uncertainty Analysis of Carbon Emission Baselines in Service Scenarios

## 1. What this repository does
This repository quantifies the uncertainty in the baseline carbon footprint of nine typical offline service scenarios: invoice issuance, e-invoice issuance, card registration, general inquiries, processing, payments, loan issuance, financial transfers, and repayment. The motivation is that moving services from physical (offline) to digital (online) channels changes their emissions, and the offline baseline needs to be known together with its uncertainty range before any comparison is drawn.

Two sources of variability matter here. Customer travel distance and physical material use (paper, SIM cards) differ a lot between individual transactions. The emission factors taken from secondary LCA databases also carry their own uncertainty. A single deterministic number is therefore not enough, so we use a Monte Carlo simulation to produce a distribution and confidence intervals for the per-transaction emission of each scenario.

## 2. Method
For each scenario, a Monte Carlo simulation runs N = 10,000 iterations. The total baseline emission per transaction is the sum over its emission sources:

$$E_{total} = \sum_{i} (AD_i \times EF_i)$$

where $AD_i$ is the activity data (mass, distance, or units) and $EF_i$ is the corresponding emission factor for component $i$.

### Parameter distributions
Each parameter is assigned a normal distribution. The relative standard deviation (RSD) is taken from standard LCA data-quality guidance:
- **Transport distance:** RSD 20% — travel behaviour varies widely across customers, geography, and infrastructure.
- **Paper / SIM cards:** RSD 10% — supply chains for standardised materials are more controlled than human behaviour.
- **Transport emission factor:** RSD 10% — reflects uncertainty about fleet efficiency and operating conditions.
- **Material emission factor:** RSD 5% — secondary LCA factors for standard industrial products are more certain.

Distributions are truncated at zero so no physically impossible negative values are drawn.

## 3. Data
Inputs come from `data9.xlsx`. The file holds, per scenario:
- **Scenario name** (e.g. "Offline loan", "Offline card registration")
- **Emission sources** (material use, transport, ...)
- **Activity data (TF):** baseline usage per process (grams of paper, distance travelled, ...)
- **Emission factor (EF):** carbon intensity in kgCO₂e per unit
- **Baseline emission (BE):** the static deterministic value, used to back-check the parameters

## 4. Outputs
`analysis.py` runs the simulation and writes:
- `all_scenarios_results.csv` — mean and 95% CI per scenario
- `markdown_table_output.txt` — the same table in Markdown
- `KDE_<Scenario>.png` (9 files, 600 dpi) — probability density per scenario with mean and 95% CI marked
- `KDE_Grid_9_Scenarios.png` / `.pdf` — a 3×3 grid of all nine scenarios

Example result table (from the 9-scenario dataset):
| Scenario | Mean CE (gCO₂e) | 95% CI (gCO₂e) |
|----------|-------------------|-------------------|
| Offline_invoice | 298.55 | [177.67, 433.12] |
| Offline_einvoice | 294.62 | [170.21, 428.79] |
| Offline_card_registration | 317.77 | [192.52, 453.18] |
| Offline_inquiry | 238.22 | [146.48, 338.16] |
| Offline_processing | 237.37 | [146.61, 338.01] |
| Offline_payment | 302.82 | [180.34, 437.53] |
| Offline_loan | 398.78 | [284.70, 524.81] |
| Offline_transfer | 268.92 | [159.43, 389.57] |
| Offline_Repayment | 267.14 | [157.49, 389.10] |

## 5. Usage
Prerequisites:
```bash
bash install_fonts.sh   # installs Times New Roman for figure typography
pip install pandas numpy matplotlib scipy openpyxl
```
Run:
```bash
python analysis.py
```
This processes all 9 scenarios from `data9.xlsx` and writes the files listed above into the repository directory.
