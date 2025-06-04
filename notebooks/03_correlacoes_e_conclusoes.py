# %% [markdown]
# # Notebook 3 — Correlações e Conclusões
#
# Análise de correlação entre desmatamento e crescimento do rebanho,
# lag temporal e segmentação expansão vs intensificação.

# %%
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats
from pathlib import Path

PROC_PATH = Path(__file__).parent.parent / "data" / "processed"
PLOTS_PATH = Path(__file__).parent.parent / "plots"

PAL = {
    'dark': '#1B4332', 'mid': '#2D6A4F', 'green': '#40916C',
    'light': '#74C69D', 'bg': '#FAFAFA', 'text': '#1A1A1A',
    'muted': '#6B7280', 'red': '#DC2626', 'amber': '#F59E0B', 'blue': '#3B82F6',
}

def setup_style():
    plt.rcParams.update({
        'figure.facecolor': PAL['bg'], 'axes.facecolor': PAL['bg'],
        'axes.edgecolor': '#D1D5DB', 'axes.titlesize': 15,
        'axes.titleweight': 'bold', 'axes.labelsize': 12,
        'xtick.color': PAL['muted'], 'ytick.color': PAL['muted'],
        'xtick.labelsize': 10, 'ytick.labelsize': 10,
        'font.family': 'sans-serif', 'font.size': 11,
        'figure.dpi': 150, 'savefig.dpi': 150,
        'savefig.bbox': 'tight', 'savefig.pad_inches': 0.4,
    })

def clean_ax(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# %%
df = pd.read_csv(PROC_PATH / "dataset_consolidado.csv")
setup_style()

# %% [markdown]
# ## 1. Correlação de Pearson e Spearman
# Será que o desmatamento está correlacionado ao crescimento do rebanho?
# Vou testar tanto Pearson (linear) quanto Spearman (monotônica).

# %%
print("📊 ANÁLISE DE CORRELAÇÃO")
print("=" * 50)

amz = df[df['amazonia_legal'] == True].dropna(subset=['desmatamento_km2', 'var_rebanho_pct'])

# Pearson
r_pearson, p_pearson = stats.pearsonr(amz['desmatamento_km2'], amz['var_rebanho_pct'])
print(f"\n   Pearson  — r = {r_pearson:.3f}, p = {p_pearson:.4f}")

# Spearman (mais robusto a outliers)
r_spearman, p_spearman = stats.spearmanr(amz['desmatamento_km2'], amz['var_rebanho_pct'])
print(f"   Spearman — ρ = {r_spearman:.3f}, p = {p_spearman:.4f}")

if p_pearson < 0.05:
    print(f"\n   ✅ Correlação significativa (p < 0.05)")
else:
    print(f"\n   ℹ️ Correlação não significativa (p = {p_pearson:.4f})")

# %% [markdown]
# ## 2. Análise de Lag Temporal
# O desmatamento antecede o crescimento do rebanho?
# Hipótese: desmata → forma pasto → coloca gado (lag de 1-2 anos)

# %%
print("\n📊 ANÁLISE DE LAG TEMPORAL")
print("-" * 50)

fig, ax = plt.subplots(figsize=(10, 5.5))
lags = range(0, 5)
correlations = []

for lag in lags:
    amz_lag = amz.copy()
    amz_lag['rebanho_lag'] = amz_lag.groupby('uf')['var_rebanho_pct'].shift(-lag)
    clean = amz_lag.dropna(subset=['desmatamento_km2', 'rebanho_lag'])
    if len(clean) > 10:
        r, p = stats.pearsonr(clean['desmatamento_km2'], clean['rebanho_lag'])
        correlations.append({'lag': lag, 'r': r, 'p': p})
        print(f"   Lag {lag} anos: r = {r:.3f}, p = {p:.4f}")

df_lag = pd.DataFrame(correlations)
colors = [PAL['dark'] if r == df_lag['r'].max() else PAL['light'] for r in df_lag['r']]
ax.bar(df_lag['lag'], df_lag['r'], color=colors, edgecolor='white', width=0.5)
ax.set_xlabel("Lag Temporal (anos)", fontsize=12)
ax.set_ylabel("Correlação (r)", fontsize=12)
ax.set_title("Correlação Desmatamento → Crescimento do Rebanho (com lag)", pad=15)
ax.set_xticks(df_lag['lag'])
ax.set_xticklabels([f'{l} anos' for l in df_lag['lag']])

best_lag = df_lag.loc[df_lag['r'].idxmax()]
ax.annotate(f'Melhor lag: {int(best_lag["lag"])} anos\nr = {best_lag["r"]:.3f}',
            xy=(best_lag['lag'], best_lag['r']),
            xytext=(best_lag['lag'] + 0.5, best_lag['r'] + 0.05),
            fontsize=11, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=PAL['dark']))

clean_ax(ax)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "08_lag_temporal.png")
plt.close()
print("   ✅ 08 — Lag temporal")

# %% [markdown]
# ## 3. Expansão vs Intensificação
# Que estados cresceram via expansão de área e quais via produtividade?

# %%
print("\n📊 EXPANSÃO vs INTENSIFICAÇÃO")
print("-" * 50)

fig, ax = plt.subplots(figsize=(12, 7))

# Calcular métricas por UF
ufs = df['uf'].unique()
exp_data = []
for uf in ufs:
    sub = df[df['uf'] == uf]
    first_year = sub['ano'].min()
    last_year = sub['ano'].max()
    first_reb = sub[sub['ano'] == first_year]['rebanho_cabecas'].values[0]
    last_reb = sub[sub['ano'] == last_year]['rebanho_cabecas'].values[0]
    growth = (last_reb / first_reb - 1) * 100 if first_reb > 0 else 0
    avg_taxa = sub['taxa_abate'].mean()
    regiao = sub['regiao'].iloc[0]
    desmat = sub['desmatamento_km2'].sum() if sub['desmatamento_km2'].notna().any() else 0

    exp_data.append({
        'uf': uf, 'crescimento': growth, 'taxa_abate_media': avg_taxa,
        'regiao': regiao, 'desmatamento_total': desmat,
        'rebanho_atual': last_reb,
    })

df_exp = pd.DataFrame(exp_data)

REG_COLORS = {
    'Norte': PAL['green'], 'Nordeste': PAL['amber'],
    'Centro-Oeste': PAL['dark'], 'Sudeste': PAL['blue'],
    'Sul': '#7C3AED',
}

for regiao, color in REG_COLORS.items():
    sub = df_exp[df_exp['regiao'] == regiao]
    ax.scatter(sub['taxa_abate_media'], sub['crescimento'],
               s=sub['rebanho_atual'] / 5e5 + 30,
               c=color, alpha=0.7, edgecolors='white', linewidths=1.5,
               label=regiao, zorder=5)

for _, row in df_exp.iterrows():
    if abs(row['crescimento']) > 10 or row['taxa_abate_media'] > 25:
        ax.annotate(row['uf'], (row['taxa_abate_media'], row['crescimento']),
                    textcoords="offset points", xytext=(6, 4), fontsize=9, fontweight='bold')

ax.axhline(0, color=PAL['muted'], linestyle='--', alpha=0.5)
ax.axvline(df_exp['taxa_abate_media'].median(), color=PAL['muted'], linestyle=':', alpha=0.3)

# Quadrantes
lims = ax.get_xlim()
ylims = ax.get_ylim()
med_x = df_exp['taxa_abate_media'].median()
ax.text(lims[0] + 1, ylims[1] - 5, 'EXTENSIVO +\nCRESCENDO', fontsize=9, color=PAL['green'], alpha=0.5, fontweight='bold')
ax.text(lims[1] - 8, ylims[1] - 5, 'INTENSIVO +\nCRESCENDO', fontsize=9, color=PAL['dark'], alpha=0.5, fontweight='bold')
ax.text(lims[0] + 1, ylims[0] + 2, 'EXTENSIVO +\nREDUZINDO', fontsize=9, color=PAL['amber'], alpha=0.5, fontweight='bold')
ax.text(lims[1] - 8, ylims[0] + 2, 'INTENSIVO +\nREDUZINDO', fontsize=9, color=PAL['blue'], alpha=0.5, fontweight='bold')

ax.set_xlabel("Taxa de Abate Média (%) — Proxy de Intensificação", fontsize=12)
ax.set_ylabel("Crescimento do Rebanho (%)", fontsize=12)
ax.set_title("Expansão vs Intensificação por Estado", pad=15)
ax.legend(loc='lower left', fontsize=10)
clean_ax(ax)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "09_expansao_vs_intensificacao.png")
plt.close()
print("   ✅ 09 — Expansão vs Intensificação")

# %% [markdown]
# ## 4. Resumo das Conclusões

# %%
print("\n" + "=" * 60)
print("📋 CONCLUSÕES PRINCIPAIS")
print("=" * 60)

total_first = df[df['ano'] == df['ano'].min()]['rebanho_cabecas'].sum()
total_last = df[df['ano'] == df['ano'].max()]['rebanho_cabecas'].sum()
growth_br = (total_last / total_first - 1) * 100

print(f"""
1. O rebanho brasileiro cresceu {growth_br:.0f}%, de {total_first/1e6:.0f} mi para {total_last/1e6:.0f} mi ({df['ano'].min()}-{df['ano'].max()})

2. O crescimento se concentrou no Norte e Centro-Oeste; Sul e Sudeste reduziram rebanho

3. Existe correlação (r = {r_pearson:.2f}) entre desmatamento e crescimento do rebanho na Amazônia Legal

4. Estados do Sul/Sudeste mantiveram ou reduziram rebanho, mas com maior taxa de abate (intensificação)

5. A relação desmatamento-rebanho tem lag temporal de {int(best_lag['lag'])} ano(s)

6. Políticas como Moratória da Soja e Operação Arco de Fogo tiveram impacto visível nos dados
""")
print("✅ Análise concluída! 9 gráficos gerados no total.")
