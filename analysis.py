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

def load_data(filepath):
    df = pd.read_excel(filepath)
    # Fill forward the scenario names so every row has its corresponding scenario
    scenario_col = '场景名称 (Scenario)'
    if scenario_col in df.columns:
        df[scenario_col] = df[scenario_col].ffill()

    # We only care about rows that have an emission source
    if '排放源' in df.columns:
        df = df.dropna(subset=['排放源'])

    return df, scenario_col

def run_simulation(df, scenario_col, N=10000):
    scenarios = df[scenario_col].unique()
    results = []
    all_scenario_data = {}

    for scenario in scenarios:
        # Clean scenario name for file saving (e.g. "Offline invoice(线下纸质发票)" -> "Offline_invoice")
        # Ensure only English letters, numbers, and underscores are kept
        base_name = str(scenario).split('(')[0].strip().replace(' ', '_')
        clean_scenario_name = re.sub(r'[^a-zA-Z0-9_]', '', base_name)
        if clean_scenario_name.endswith('_'):
            clean_scenario_name = clean_scenario_name[:-1]

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
            elif '纸张' in source or '电话卡' in source or '纸' in source or '卡' in source:
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

        # Kernel density estimation
        kde = stats.gaussian_kde(total_emissions)
        x_range = np.linspace(total_emissions.min(), total_emissions.max(), 500)
        kde_vals = kde(x_range)

        res_dict = {
            'Scenario': clean_scenario_name,
            'Original_Scenario': scenario,
            'Mean CE (gCO2e)': ce_mean,
            'Std Dev (gCO2e)': ce_std,
            '95% CI Lower (gCO2e)': ci_lower,
            '95% CI Upper (gCO2e)': ci_upper,
            'total_emissions': total_emissions,
            'x_range': x_range,
            'kde_vals': kde_vals
        }
        results.append(res_dict)
        all_scenario_data[clean_scenario_name] = res_dict

    return results, all_scenario_data

def plot_single_kde(scenario_data):
    clean_scenario_name = scenario_data['Scenario']
    ce_mean = scenario_data['Mean CE (gCO2e)']
    ci_lower = scenario_data['95% CI Lower (gCO2e)']
    ci_upper = scenario_data['95% CI Upper (gCO2e)']
    x_range = scenario_data['x_range']
    kde_vals = scenario_data['kde_vals']

    fig, ax = plt.subplots(figsize=(8, 6), dpi=600)

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

def plot_grid_kde(all_scenario_data):
    fig, axes = plt.subplots(3, 3, figsize=(15, 15), dpi=600)
    fig.suptitle('Probability Distribution of Carbon Emissions Across 9 Scenarios', fontsize=18, fontweight='bold')

    # Flatten the 3x3 axes array
    axes = axes.flatten()

    scenarios = list(all_scenario_data.keys())

    for i, ax in enumerate(axes):
        if i < len(scenarios):
            scenario_name = scenarios[i]
            data = all_scenario_data[scenario_name]

            x_range = data['x_range']
            kde_vals = data['kde_vals']
            ce_mean = data['Mean CE (gCO2e)']
            ci_lower = data['95% CI Lower (gCO2e)']
            ci_upper = data['95% CI Upper (gCO2e)']

            # Plot KDE curve with fill
            ax.plot(x_range, kde_vals, color=COLOR_KDE_LINE, linewidth=1.5)
            ax.fill_between(x_range, kde_vals, color=COLOR_KDE_FILL, alpha=0.4)

            # Vertical lines for Mean and 95% CI
            ax.axvline(ce_mean, color='#333333', linestyle='dashed', linewidth=1.5)
            ax.axvline(ci_lower, color='#555555', linestyle='dotted', linewidth=1.5)
            ax.axvline(ci_upper, color='#555555', linestyle='dotted', linewidth=1.5)

            y_max = max(kde_vals)
            ax.set_ylim(0, y_max * 1.15)

            # Stats text box
            stats_text = f"Mean: {ce_mean:.1f}\n95% CI: [{ci_lower:.1f}, {ci_upper:.1f}]"
            ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='#cccccc'))

            # Aesthetics
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#333333')
            ax.spines['bottom'].set_color('#333333')
            ax.tick_params(colors='#333333', labelsize=10)

            title_name = scenario_name.replace('_', ' ')
            ax.set_title(title_name, fontsize=14, pad=10, color='#333333')

            if i >= 6: # Bottom row
                ax.set_xlabel('Total Emissions (gCO$_2$e/transaction)', fontsize=12, color='#333333')
            if i % 3 == 0: # Left column
                ax.set_ylabel('Probability Density', fontsize=12, color='#333333')
        else:
            ax.axis('off')

    # Add a global legend at the bottom
    legend_elements = [
        plt.Line2D([0], [0], color=COLOR_KDE_LINE, linewidth=1.5, label='KDE Curve'),
        plt.Line2D([0], [0], color='#333333', linestyle='dashed', linewidth=1.5, label='Mean'),
        plt.Line2D([0], [0], color='#555555', linestyle='dotted', linewidth=1.5, label='95% CI')
    ]

    fig.legend(handles=legend_elements, loc='lower center', ncol=3, bbox_to_anchor=(0.5, 0.02), fontsize=12, frameon=False)

    plt.tight_layout()
    # Adjust subplots to make room for global title and legend
    fig.subplots_adjust(top=0.92, bottom=0.08, hspace=0.3, wspace=0.25)

    plt.savefig('KDE_Grid_9_Scenarios.png', dpi=600, transparent=True, bbox_inches='tight')
    plt.savefig('KDE_Grid_9_Scenarios.pdf', dpi=600, transparent=True, bbox_inches='tight')
    plt.close()
    print("Saved KDE_Grid_9_Scenarios.png and KDE_Grid_9_Scenarios.pdf")

def main():
    np.random.seed(42)
    excel_file = 'data9.xlsx'

    print(f"Loading data from {excel_file}...")
    df, scenario_col = load_data(excel_file)

    print("Running Monte Carlo Simulations...")
    results, all_scenario_data = run_simulation(df, scenario_col, N=10000)

    print("Generating Single KDE Plots...")
    for res in results:
        scenario_name = res['Scenario']
        print(f"Plotting Single KDE for {scenario_name}")
        plot_single_kde(res)

    print("Generating 3x3 Grid KDE Plot...")
    plot_grid_kde(all_scenario_data)

    # Save results to CSV
    # Create a DataFrame but drop the heavy lists to save cleanly to CSV
    save_results = []
    for r in results:
        save_results.append({
            'Scenario': r['Scenario'],
            'Original_Scenario': r['Original_Scenario'],
            'Mean CE (gCO2e)': r['Mean CE (gCO2e)'],
            'Std Dev (gCO2e)': r['Std Dev (gCO2e)'],
            '95% CI Lower (gCO2e)': r['95% CI Lower (gCO2e)'],
            '95% CI Upper (gCO2e)': r['95% CI Upper (gCO2e)']
        })
    df_results = pd.DataFrame(save_results)
    df_results.to_csv('all_scenarios_results.csv', index=False)
    print("\nSaved all_scenarios_results.csv")

    # Generate Markdown table
    md_table = "| Scenario | Mean CE (gCO$_2$e) | 95% CI (gCO$_2$e) |\n"
    md_table += "|----------|-------------------|-------------------|\n"
    for res in save_results:
        md_table += f"| {res['Scenario']} | {res['Mean CE (gCO2e)']:.2f} | [{res['95% CI Lower (gCO2e)']:.2f}, {res['95% CI Upper (gCO2e)']:.2f}] |\n"

    with open('markdown_table_output.txt', 'w') as f:
        f.write(md_table)

    print("Saved markdown_table_output.txt for README.md inclusion")
    print("\nGenerated Markdown Table:\n")
    print(md_table)

if __name__ == '__main__':
    main()
