import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import re

# Set Nature journal publication standards for fonts
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'Times New Roman'

# 1. Load Data
excel_file = '线下贷款.xlsx'
df = pd.read_excel(excel_file, sheet_name='线下贷款')

def extract_number(val):
    if pd.isna(val): return 0.0
    val_str = str(val).replace(',', '')
    match = re.search(r'([\d\.]+)', val_str)
    return float(match.group(1)) if match else 0.0

# Extract parameters dynamically
paper_weight_base = 0.0
paper_ef_base = 0.0
transport_dist_base = 0.0
transport_ef_base = 0.0

col_0 = df.columns[0]
for _, row in df.iterrows():
    name = str(row[col_0])
    if '纸张' in name:
        paper_weight_base = extract_number(row.iloc[2])
        # Current unit is kgCO2/t -> gCO2e/g
        # 1 kgCO2/t = 1000 gCO2 / 10^6 g = 0.001 gCO2/g
        paper_ef_base = extract_number(row.iloc[3]) / 1000.0
    elif '出行' in name:
        transport_dist_base = extract_number(row.iloc[2])
        # Current unit is kgCO2e/人公里 -> gCO2e/km
        # 1 kgCO2e = 1000 gCO2e
        transport_ef_base = extract_number(row.iloc[3]) * 1000.0

print("Baseline Parameters:")
print(f"Paper Weight: {paper_weight_base:.4f} g")
print(f"Paper EF: {paper_ef_base:.4f} gCO2e/g")
print(f"Transport Dist: {transport_dist_base:.4f} km")
print(f"Transport EF: {transport_ef_base:.4f} gCO2e/km")

# 2. Uncertainty Analysis Setup
np.random.seed(42)
N = 10000

# Define distributions (Normal)
# Parameter: (Mean, Std Dev relative to Mean)
params = {
    'Paper Weight': {'mean': paper_weight_base, 'std_rel': 0.10},
    'Paper EF': {'mean': paper_ef_base, 'std_rel': 0.05},
    'Transport Distance': {'mean': transport_dist_base, 'std_rel': 0.20},
    'Transport EF': {'mean': transport_ef_base, 'std_rel': 0.10}
}

# Generate samples
samples = {}
for name, p in params.items():
    std_dev = p['mean'] * p['std_rel']
    # Ensure non-negative values
    dist = np.random.normal(p['mean'], std_dev, N)
    dist = np.maximum(dist, 0) # Clip at 0 just in case
    samples[name] = dist

# Create DataFrame of samples
df_sim = pd.DataFrame(samples)

# 3. Calculate Carbon Emissions (CE) for each iteration
# CE = Paper_Emission + Transport_Emission
# Component Emissions = Activity Data * Emission Factor

df_sim['Paper_Emission'] = df_sim['Paper Weight'] * df_sim['Paper EF']
df_sim['Transport_Emission'] = df_sim['Transport Distance'] * df_sim['Transport EF']
df_sim['Total_CE'] = df_sim['Paper_Emission'] + df_sim['Transport_Emission']

# 4. Results Analysis
ce_mean = df_sim['Total_CE'].mean()
ce_std = df_sim['Total_CE'].std()
ci_lower = np.percentile(df_sim['Total_CE'], 2.5)
ci_upper = np.percentile(df_sim['Total_CE'], 97.5)

print("\nResults:")
print(f"Mean CE: {ce_mean:.4f} gCO2e")
print(f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}] gCO2e")

# Save results to text file
with open('analysis_results.txt', 'w') as f:
    f.write("Uncertainty Analysis Results (Offline Loan)\n")
    f.write("======================================================\n")
    f.write(f"Mean Carbon Emissions: {ce_mean:.4f} gCO2e/transaction\n")
    f.write(f"Standard Deviation: {ce_std:.4f} gCO2e\n")
    f.write(f"95% Confidence Interval: [{ci_lower:.4f}, {ci_upper:.4f}] gCO2e\n")
    f.write("\nInput Parameters (Mean, Rel Std):\n")
    for name, p in params.items():
        f.write(f"{name}: Mean={p['mean']:.4f}, Rel Std={p['std_rel']*100}%\n")

# 5. Visualizations

# Professional color palette (Nature journal friendly)
COLOR_KDE_LINE = '#1c5e7b' # Elegant deep blue
COLOR_KDE_FILL = '#5b92aa' # Soft blue-grey
COLOR_BAR_LOW = '#a8c2d1'  # Soft light blue for min-to-base
COLOR_BAR_HIGH = '#d7a28e' # Soft muted terracotta for base-to-max

# 5.1 KDE Plot (Probability Distribution)
fig, ax = plt.subplots(figsize=(8, 6), dpi=600)

kde = stats.gaussian_kde(df_sim['Total_CE'])
x_range = np.linspace(df_sim['Total_CE'].min(), df_sim['Total_CE'].max(), 500)
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

# Use a clean legend for statistics instead of complex staggered text annotations
legend_stats = [
    plt.Line2D([0], [0], color='#333333', linestyle='dashed', linewidth=1.5, label=f'Mean: {ce_mean:.1f}'),
    plt.Line2D([0], [0], color='#555555', linestyle='dotted', linewidth=1.5, label=f'95% CI: [{ci_lower:.1f}, {ci_upper:.1f}]')
]
ax.legend(handles=legend_stats, loc='upper right', frameon=False, fontsize=11)

# Extend y-axis slightly to fit nicely
ax.set_ylim(0, y_max * 1.15)

# Aesthetics
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#333333')
ax.spines['bottom'].set_color('#333333')
ax.tick_params(colors='#333333')
ax.set_title('Probability Distribution of Total Carbon Emissions', fontsize=14, fontweight='bold', pad=25, color='#333333')
ax.set_xlabel('Total Carbon Emissions (gCO$_2$e/transaction)', fontsize=12, color='#333333')
ax.set_ylabel('Probability Density', fontsize=12, color='#333333')

plt.tight_layout()
plt.savefig('histogram_er_updated.png', dpi=600, transparent=True, bbox_inches='tight')
print("Saved histogram_er_updated.png (KDE plot)")

# 5.2 Tornado Plot (Sensitivity Analysis)
base_ce = (paper_weight_base * paper_ef_base +
           transport_dist_base * transport_ef_base)

sensitivity_data = []

for name, p in params.items():
    # P10 and P90 values for this parameter
    p10_val = stats.norm.ppf(0.10, loc=p['mean'], scale=p['mean']*p['std_rel'])
    p90_val = stats.norm.ppf(0.90, loc=p['mean'], scale=p['mean']*p['std_rel'])

    # Calculate CE with P10 value (others at mean)
    vals = {k: params[k]['mean'] for k in params}

    # Low Case
    vals[name] = p10_val
    ce_low = (vals['Paper Weight'] * vals['Paper EF'] +
              vals['Transport Distance'] * vals['Transport EF'])

    # High Case
    vals[name] = p90_val
    ce_high = (vals['Paper Weight'] * vals['Paper EF'] +
               vals['Transport Distance'] * vals['Transport EF'])

    sensitivity_data.append({
        'Parameter': name,
        'Low': ce_low,
        'High': ce_high,
        'Range': abs(ce_high - ce_low),
        'Min': min(ce_low, ce_high),
        'Max': max(ce_low, ce_high)
    })

# Sort by range
sensitivity_df = pd.DataFrame(sensitivity_data).sort_values('Range', ascending=True)

# Append sensitivity ranking to results file
with open('analysis_results.txt', 'a') as f:
    f.write("\nSensitivity Analysis Ranking (Range of CE when varying P10-P90):\n")
    for i, row in sensitivity_df.sort_values('Range', ascending=False).iterrows():
        f.write(f"{row['Parameter']}: Range={row['Range']:.4f} gCO2e (Low={row['Low']:.4f}, High={row['High']:.4f})\n")

fig, ax = plt.subplots(figsize=(12, 6), dpi=600)
fig.subplots_adjust(left=0.4, right=0.85, bottom=0.2) # Ensure horizontal space and bottom breathing room for legend
y_pos = np.arange(len(sensitivity_df))
sensitivity_df_reset = sensitivity_df.reset_index(drop=True)

bar_height = 0.4 # Narrow bars for "breathing room"

for i, row in sensitivity_df_reset.iterrows():
    val_min = row['Min']
    val_max = row['Max']

    # Left segment: Min to Base Case
    if val_min < base_ce:
        ax.barh(i, base_ce - val_min, left=val_min, height=bar_height, color=COLOR_BAR_LOW, edgecolor='#333333', linewidth=0.8)
    # Right segment: Base Case to Max
    if val_max > base_ce:
        ax.barh(i, val_max - base_ce, left=base_ce, height=bar_height, color=COLOR_BAR_HIGH, edgecolor='#333333', linewidth=0.8)

# Add baseline
ax.axvline(base_ce, color='#333333', linestyle='-', linewidth=1.5, label='Baseline')

# Aesthetics
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#333333')
ax.spines['bottom'].set_color('#333333')
ax.tick_params(colors='#333333')

ax.set_yticks(y_pos)
ax.set_yticklabels(sensitivity_df_reset['Parameter'], fontsize=12)
ax.set_xlabel('Total Carbon Emissions (gCO$_2$e/transaction)', fontsize=12, color='#333333')
ax.set_title('Tornado Sensitivity Chart (Impact on Carbon Emissions)', fontsize=14, fontweight='bold', pad=15, color='#333333')

# Custom legend for the dual-tone
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
legend_elements = [
    Patch(facecolor=COLOR_BAR_LOW, edgecolor='#333333', linewidth=0.5, label='Low Case (P10)'),
    Patch(facecolor=COLOR_BAR_HIGH, edgecolor='#333333', linewidth=0.5, label='High Case (P90)'),
    Line2D([0], [0], color='#333333', linewidth=1.5, linestyle='-', label='Baseline Mean')
]
# Move legend completely outside the plot area below the X-axis
ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, fontsize=11)

# Calculate global min/max for dynamic text offsetting and forced padding
global_min = sensitivity_df_reset['Min'].min()
global_max = sensitivity_df_reset['Max'].max()

margin = (global_max - global_min) * 0.15
ax.set_xlim(global_min - margin, global_max + margin)

# Add value labels completely outside the bars safely using margin/4 offset
for i, row in sensitivity_df_reset.iterrows():
    ax.text(row['Min'] - (margin/4), i, f"{row['Min']:.1f}", va='center', ha='right', fontsize=10, color='#333333')
    ax.text(row['Max'] + (margin/4), i, f"{row['Max']:.1f}", va='center', ha='left', fontsize=10, color='#333333')

plt.savefig('tornado_sensitivity_updated.png', dpi=600, transparent=True, bbox_inches='tight')
print("Saved tornado_sensitivity_updated.png (Dual-tone Tornado plot)")
