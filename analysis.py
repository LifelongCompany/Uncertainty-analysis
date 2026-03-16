import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import re
import os

# Set Nature journal publication standards for fonts
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'Times New Roman'

# Professional color palette (Nature journal friendly)
COLOR_KDE_LINE = '#1c5e7b' # Elegant deep blue
COLOR_KDE_FILL = '#5b92aa' # Soft blue-grey

def extract_number(val):
    if pd.isna(val): return 0.0
    val_str = str(val).replace(',', '')
    match = re.search(r'([\d\.]+)', val_str)
    return float(match.group(1)) if match else 0.0

# 1. Load Data
excel_file = '线下场景碳排放数据提取.xlsx'
df = pd.read_excel(excel_file)

# Fill forward the scenario names so every row has its corresponding scenario
scenario_col = '场景名称 (Scenario)'
df[scenario_col] = df[scenario_col].ffill()

# We only care about rows that have an emission source
df = df.dropna(subset=['排放源'])

scenarios = df[scenario_col].unique()

results = []

np.random.seed(42)
N = 10000

for scenario in scenarios:
    # Clean scenario name for file saving (e.g. "Offline invoice(线下纸质发票)" -> "Offline_invoice")
    clean_scenario_name = scenario.split('(')[0].strip().replace(' ', '_')

    print(f"\nProcessing Scenario: {clean_scenario_name}")

    scenario_data = df[df[scenario_col] == scenario]

    # Store parameter distributions
    params = {}

    for _, row in scenario_data.iterrows():
        source = str(row['排放源'])
        tf = extract_number(row['活动数据 TF(g/次, km/次, 张)'])
        ef = extract_number(row['排放因子 EF(kgCO2e/t, kgCO2e/人公里)'])
        be = extract_number(row['基准线排放 BE(gCO2e)'])

        # Determine RSD based on source
        if '出行' in source:
            tf_rsd = 0.20
            ef_rsd = 0.10
        elif '纸张' in source or '电话卡' in source:
            tf_rsd = 0.10
            ef_rsd = 0.05
        else:
            tf_rsd = 0.10
            ef_rsd = 0.05

        # Unit conversion logic: TF * converted_EF = BE
        # If BE is provided and > 0, we can back-calculate the effective EF in consistent units
        if tf > 0 and be > 0:
            converted_ef = be / tf
        else:
            converted_ef = 0.0

        params[source] = {
            'tf_mean': tf, 'tf_rsd': tf_rsd,
            'ef_mean': converted_ef, 'ef_rsd': ef_rsd
        }

    # Generate samples
    total_emissions = np.zeros(N)

    for source, p in params.items():
        # Generate TF samples
        tf_std = p['tf_mean'] * p['tf_rsd']
        tf_samples = np.random.normal(p['tf_mean'], tf_std, N)
        tf_samples = np.maximum(tf_samples, 0)

        # Generate EF samples
        ef_std = p['ef_mean'] * p['ef_rsd']
        ef_samples = np.random.normal(p['ef_mean'], ef_std, N)
        ef_samples = np.maximum(ef_samples, 0)

        # Calculate emissions for this source and add to total
        source_emissions = tf_samples * ef_samples
        total_emissions += source_emissions

    # Calculate statistics
    ce_mean = total_emissions.mean()
    ce_std = total_emissions.std()
    ci_lower = np.percentile(total_emissions, 2.5)
    ci_upper = np.percentile(total_emissions, 97.5)

    results.append({
        'Scenario': clean_scenario_name,
        'Mean CE (gCO2e)': ce_mean,
        'Std Dev (gCO2e)': ce_std,
        '95% CI Lower (gCO2e)': ci_lower,
        '95% CI Upper (gCO2e)': ci_upper
    })

    # 5. Visualizations: KDE Plot
    fig, ax = plt.subplots(figsize=(8, 6), dpi=600)

    kde = stats.gaussian_kde(total_emissions)
    x_range = np.linspace(total_emissions.min(), total_emissions.max(), 500)
    kde_vals = kde(x_range)

    # Plot KDE curve with fill
    ax.plot(x_range, kde_vals, color=COLOR_KDE_LINE, linewidth=2)
    ax.fill_between(x_range, kde_vals, color=COLOR_KDE_FILL, alpha=0.4)

    # Vertical lines for Mean and 95% CI
    ax.axvline(ce_mean, color='#333333', linestyle='dashed', linewidth=1.5)
    ax.axvline(ci_lower, color='#555555', linestyle='dotted', linewidth=1.5)
    ax.axvline(ci_upper, color='#555555', linestyle='dotted', linewidth=1.5)

    # Calculate optimal y-position for annotations
    y_max = max(kde_vals)

    # Clean legend for statistics
    legend_stats = [
        plt.Line2D([0], [0], color='#333333', linestyle='dashed', linewidth=1.5, label=f'Mean: {ce_mean:.1f}'),
        plt.Line2D([0], [0], color='#555555', linestyle='dotted', linewidth=1.5, label=f'95% CI: [{ci_lower:.1f}, {ci_upper:.1f}]')
    ]
    ax.legend(handles=legend_stats, loc='upper right', frameon=False, fontsize=11)

    # Extend y-axis slightly
    ax.set_ylim(0, y_max * 1.15)

    # Aesthetics
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.tick_params(colors='#333333')

    title_name = clean_scenario_name.replace('_', ' ')
    ax.set_title(f'Probability Distribution of Carbon Emissions\n({title_name})', fontsize=14, fontweight='bold', pad=25, color='#333333')
    ax.set_xlabel('Total Carbon Emissions (gCO$_2$e/transaction)', fontsize=12, color='#333333')
    ax.set_ylabel('Probability Density', fontsize=12, color='#333333')

    plt.tight_layout()
    filename = f'KDE_{clean_scenario_name}.png'
    plt.savefig(filename, dpi=600, transparent=True, bbox_inches='tight')
    plt.close()
    print(f"Saved {filename}")

# Save results to CSV
df_results = pd.DataFrame(results)
df_results.to_csv('all_scenarios_results.csv', index=False)
print("\nSaved all_scenarios_results.csv")

# Generate Markdown table
md_table = "| Scenario | Mean CE (gCO$_2$e) | 95% CI (gCO$_2$e) |\n"
md_table += "|----------|-------------------|-------------------|\n"
for res in results:
    md_table += f"| {res['Scenario']} | {res['Mean CE (gCO2e)']:.2f} | [{res['95% CI Lower (gCO2e)']:.2f}, {res['95% CI Upper (gCO2e)']:.2f}] |\n"

with open('markdown_table_output.txt', 'w') as f:
    f.write(md_table)

print("Saved markdown_table_output.txt for README.md inclusion")
print("\nGenerated Markdown Table:\n")
print(md_table)
