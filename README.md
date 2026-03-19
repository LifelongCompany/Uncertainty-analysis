# Uncertainty Analysis of Carbon Emission Baselines in Service Scenarios: A Stochastic Modeling Approach

## 1. Project Overview

In the context of global climate change mitigation and the operationalization of corporate sustainability mandates, the precise quantification of greenhouse gas (GHG) emissions is paramount. The transition from physical (offline) to digital (online) service modalities presents substantial emission reduction opportunities. This repository delineates a rigorous methodological assessment of the baseline carbon footprint associated with 9 typical offline service scenarios, encompassing a spectrum of activities including invoice issuance, e-invoice issuance, card registration, general inquiries, processing, payments, loan issuance, financial transfers, and repayment operations.

The primary objective of this study is to systematically evaluate the total baseline emissions generated per transaction across these diverse service ecosystems. Recognizing the inherent variability in empirical activity data—most notably customer travel distances and the consumption of physical materials (e.g., paper, SIM cards)—as well as the natural epistemological uncertainty embedded in secondary emission factors, deterministic single-point estimates are deemed insufficient. Consequently, this codebase deploys advanced stochastic modeling techniques via Python-based Monte Carlo simulations across multiple emission sources. This methodology robustly captures the statistical distribution of emission profiles, providing highly reliable confidence intervals essential for scientific publication and rigorous carbon accounting.

## 2. Methodology

To rigorously capture the intrinsic variability of the input parameters governing the physical service lifecycles across the 9 distinct scenarios, a comprehensive Monte Carlo Simulation ($N = 10,000$ iterations) is computationally executed for each scenario independently. The total baseline emission per transaction ($E_{total}$) for a given scenario is mathematically formulated as the aggregate of emissions originating from its specific constituent vectors, dynamically adapting to the presence of material consumption (e.g., paper, plastic cards) and requisite customer transportation.

The fundamental deterministic equation is defined as follows:
$$E_{total} = \sum_{i} (AD_i \times EF_i)$$
where $AD_i$ denotes the Activity Data (e.g., mass, distance, units) and $EF_i$ represents the corresponding Emission Factor for process component $i$ unique to the evaluated scenario.

### Parameter Distributions
Baseline deterministic values were systematically extracted from the primary life cycle inventory (LCI) dataset. To construct the robust stochastic framework, normal probability density functions were computationally assigned to each parameter. The relative standard deviation (RSD), acting as a proxy for the uncertainty margin, was rigorously calibrated in accordance with standard life cycle assessment (LCA) data quality rubrics, tailored to the specific nature of the emission source:

- **Activity Data (AD) Variability:**
  - **Transport Distance:** Assigned an RSD of 20%, empirically reflecting profound behavioral, geographic, and infrastructural variability inherent in customer travel.
  - **Standardized Materials (Paper / SIM Cards):** Assigned an RSD of 10%, reflecting more tightly controlled, industrial supply chain consistency compared to human behavior.
- **Emission Factor (EF) Variability:**
  - **Transport EF:** Assigned an RSD of 10%, accommodating the uncertainty surrounding the precise modalities, fleet efficiencies, and operational conditions of the transport utilized by the client base.
  - **Standardized Materials EF:** Assigned an RSD of 5%, as secondary LCA database emission factors for standard industrial products exhibit higher confidence intervals.

To maintain strict physical plausibility and logical integrity, all probability density distributions are explicitly truncated at zero via the stochastic model, precluding mathematically viable but physically impossible negative domain artifacts.

## 3. Data Source

The primary data driving the Monte Carlo simulations are extracted directly from the provided source file: `data9.xlsx`. This comprehensive dataset encapsulates the critical deterministic parameters required for all 9 scenarios. Specifically, the data architecture delineates:

- **Scenario Name:** The specific offline operational context (e.g., "Offline loan", "Offline card registration").
- **Emission Sources:** The distinct physical processes contributing to the carbon footprint (e.g., material usage, transportation).
- **Activity Data (TF):** The baseline numerical usage metric for each process (e.g., grams of paper, distance traveled).
- **Emission Factor (EF):** The corresponding carbon intensity metric ($kgCO_{2}e/unit$).
- **Baseline Emission (BE):** The static, deterministic baseline carbon footprint metric, used for computational back-calculation and parameter integrity verification.

## 4. Outputs & Visualization

The computational framework (`analysis.py`) successfully executes the Monte Carlo methodologies, yielding both raw statistical outputs and high-fidelity, publication-ready visualizations conforming strictly to top-tier academic graphical standards (e.g., Nature Journal parameters, Times New Roman typography, high resolution vector and raster graphics).

### 4.1 Probabilistic Carbon Emission Potentials
The execution generates comprehensive probability distributions identifying profound operational variances. A summary table of the computed statistical means and corresponding 95% Confidence Intervals (CI) is auto-generated during runtime and outputted as `all_scenarios_results.csv` and a markdown representation (`markdown_table_output.txt`).

Below is an example output table generated from the 9 scenario dataset:

| Scenario | Mean CE (gCO$_2$e) | 95% CI (gCO$_2$e) |
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

### 4.2 High-Resolution Visualizations
The code systematically produces distinct visual assets tailored for varied publication requirements:

1. **Individual KDE Plots:**
   For localized, specific analysis, 9 distinct Kernel Density Estimation (KDE) plots are independently generated and saved as individual `KDE_<Scenario>.png` files at $600 \text{ dpi}$. Each plot clearly maps the probability density, mean, and 95% confidence intervals natively within the figure frame.

2. **Academic $3 \times 3$ Grid Figure:**
   For comprehensive manuscript publication, a synthesized $3 \times 3$ subplot matrix (`KDE_Grid_9_Scenarios.png` and `KDE_Grid_9_Scenarios.pdf`) is autonomously assembled. This composite graphic maintains the $600 \text{ dpi}$ rigorous standards, integrates a global centralized legend to minimize graphical clutter, and isolates localized statistical data (Mean, 95% CI) into unobtrusive bounded textual overlays within each subplot.

## 5. Usage

To execute the computational model and autonomously generate the data outputs and academic visualizations, strictly follow the procedural steps below within a bash environment:

### Prerequisites Installation
Ensure your Python environment possesses the requisite libraries and that the system has installed the necessary TrueType fonts to support the Nature journal typography standards (`Times New Roman`):

```bash
# Execute the font installation script to install required Microsoft TrueType fonts
bash install_fonts.sh

# Install Python dependencies
pip install pandas numpy matplotlib scipy openpyxl
```

### Execution
With dependencies satisfied, invoke the primary analytical script from the root repository directory containing the `data9.xlsx` file:

```bash
# Run the Monte Carlo simulation and graph generation architecture
python analysis.py
```

Upon successful execution, the script will systematically process all 9 scenarios from the primary dataset, generating and depositing the following into the local directory:
- `all_scenarios_results.csv`
- `markdown_table_output.txt`
- 9 independent high-resolution `KDE_<Scenario>.png` graphical files.
- The global $3 \times 3$ composite grids `KDE_Grid_9_Scenarios.png` and `KDE_Grid_9_Scenarios.pdf`.
