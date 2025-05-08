# %% [markdown]
# # Notebook 2 — Análise Exploratória
#
# Gráficos sobre evolução do rebanho, desmatamento e produtividade

# %%
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

PROC_PATH = Path(__file__).parent.parent / "data" / "processed"
PLOTS_PATH = Path(__file__).parent.parent / "plots"
PLOTS_PATH.mkdir(exist_ok=True)

PAL = {
    'dark': '#1B4332', 'mid': '#2D6A4F', 'green': '#40916C',
    'light': '#74C69D', 'pale': '#B7E4C7',
    'bg': '#FAFAFA', 'text': '#1A1A1A', 'muted': '#6B7280',
    'red': '#DC2626', 'amber': '#F59E0B', 'blue': '#3B82F6',
    'purple': '#7C3AED',
}
REG_COLORS = {
    'Norte': PAL['green'], 'Nordeste': PAL['amber'],
    'Centro-Oeste': PAL['dark'], 'Sudeste': PAL['blue'],
    'Sul': PAL['purple'],
}

def setup_style():
    plt.rcParams.update({
        'figure.facecolor': PAL['bg'], 'axes.facecolor': PAL['bg'],
        'axes.edgecolor': '#D1D5DB', 'axes.labelcolor': PAL['text'],
        'axes.titlesize': 15, 'axes.titleweight': 'bold',
        'axes.labelsize': 12, 'xtick.color': PAL['muted'],
        'ytick.color': PAL['muted'], 'xtick.labelsize': 10,
        'ytick.labelsize': 10, 'text.color': PAL['text'],
        'font.family': 'sans-serif', 'font.size': 11,
        'figure.dpi': 150, 'savefig.dpi': 150,
        'savefig.bbox': 'tight', 'savefig.pad_inches': 0.4,
        'legend.fontsize': 10,
    })

def clean_ax(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# %%
df = pd.read_csv(PROC_PATH / "dataset_consolidado.csv")
setup_style()
print(f"📊 Dataset: {len(df)} registros")

# %% [markdown]
# ## Gráfico 1 — Evolução do Rebanho Bovino por Região

# %%
fig, ax = plt.subplots(figsize=(13, 6.5))

# Total Brasil
total = df.groupby('ano')['rebanho_cabecas'].sum() / 1e6
ax.plot(total.index, total.values, color=PAL['text'], linewidth=3, label='Brasil Total', zorder=10)

# Por região
for regiao, color in REG_COLORS.items():
    sub = df[df['regiao'] == regiao].groupby('ano')['rebanho_cabecas'].sum() / 1e6
    ax.plot(sub.index, sub.values, color=color, linewidth=2, alpha=0.8, label=regiao)

# Eventos
events = {
    2006: 'Moratória\nda Soja', 2008: 'Operação\nArco de Fogo',
    2010: 'Plano ABC', 2019: 'Aumento\nDesmatamento',
}
for year, label in events.items():
    ax.axvline(year, color=PAL['muted'], linestyle=':', alpha=0.3)
    ax.text(year, ax.get_ylim()[1] * 0.95, label, ha='center', fontsize=8,
            color=PAL['muted'], va='top')

ax.set_xlabel("Ano", fontsize=12)
ax.set_ylabel("Rebanho (Milhões de Cabeças)", fontsize=12)
ax.set_title("Evolução do Rebanho Bovino Brasileiro por Região (2004–2023)", pad=15)
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=10)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f} mi'))
clean_ax(ax)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "01_evolucao_rebanho_regiao.png")
plt.close()
print("✅ 01 — Evolução por região")

# %% [markdown]
# ## Gráfico 2 — Top 10 Estados por Rebanho (2004 vs 2023)

# %%
fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))

for i, (year, ax) in enumerate(zip([df['ano'].min(), df['ano'].max()], axes)):
    sub = df[df['ano'] == year].nlargest(10, 'rebanho_cabecas').sort_values('rebanho_cabecas')
    colors = [REG_COLORS.get(r, PAL['muted']) for r in sub['regiao']]
    bars = ax.barh(sub['uf'], sub['rebanho_cabecas'] / 1e6, color=colors, edgecolor='white', height=0.6)
    for bar, val in zip(bars, sub['rebanho_cabecas'] / 1e6):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f'{val:.1f} mi', va='center', fontsize=10, fontweight='bold')
    ax.set_title(f'Top 10 Estados — {year}', fontsize=14, fontweight='bold')
    ax.set_xlabel("Milhões de Cabeças", fontsize=11)
    ax.set_xlim(0, sub['rebanho_cabecas'].max() / 1e6 * 1.25)
    clean_ax(ax)

# Legend
import matplotlib.patches as mpatches
patches = [mpatches.Patch(color=c, label=r) for r, c in REG_COLORS.items()]
fig.legend(handles=patches, loc='lower center', ncol=5, fontsize=10, bbox_to_anchor=(0.5, -0.02))
plt.suptitle("Ranking dos Estados por Rebanho Bovino", fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "02_top10_estados.png")
plt.close()
print("✅ 02 — Top 10 estados")

# %% [markdown]
# ## Gráfico 3 — Crescimento Acumulado do Rebanho por UF

# %%
fig, ax = plt.subplots(figsize=(14, 7))

first_year = df['ano'].min()
last_year = df['ano'].max()

growth = []
for uf in df['uf'].unique():
    sub = df[df['uf'] == uf]
    first = sub[sub['ano'] == first_year]['rebanho_cabecas'].values
    last_v = sub[sub['ano'] == last_year]['rebanho_cabecas'].values
    if len(first) > 0 and len(last_v) > 0 and first[0] > 0:
        g = (last_v[0] / first[0] - 1) * 100
        growth.append({'uf': uf, 'crescimento_pct': g,
                       'regiao': sub['regiao'].iloc[0],
                       'rebanho_atual': last_v[0]})

df_growth = pd.DataFrame(growth).sort_values('crescimento_pct')
colors = [REG_COLORS.get(r, PAL['muted']) for r in df_growth['regiao']]

bars = ax.barh(df_growth['uf'], df_growth['crescimento_pct'], color=colors, edgecolor='white', height=0.65)
ax.axvline(0, color=PAL['text'], linewidth=1)

for bar, (_, row) in zip(bars, df_growth.iterrows()):
    val = row['crescimento_pct']
    pos = bar.get_width() + (2 if val >= 0 else -2)
    ha = 'left' if val >= 0 else 'right'
    ax.text(pos, bar.get_y() + bar.get_height()/2,
            f'{val:+.0f}%', va='center', ha=ha, fontsize=9, fontweight='bold')

ax.set_xlabel(f"Crescimento do Rebanho ({first_year}–{last_year}, %)", fontsize=12)
ax.set_title(f"Crescimento do Rebanho Bovino por Estado ({first_year}–{last_year})", pad=15)
patches = [mpatches.Patch(color=c, label=r) for r, c in REG_COLORS.items()]
ax.legend(handles=patches, loc='lower right', fontsize=10)
clean_ax(ax)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "03_crescimento_por_uf.png")
plt.close()
print("✅ 03 — Crescimento por UF")

# %% [markdown]
# ## Gráfico 4 — Desmatamento vs Crescimento do Rebanho (Amazônia Legal)

# %%
fig, ax = plt.subplots(figsize=(11, 7))

amz = df[df['amazonia_legal'] == True].copy()
desmat_acum = amz.groupby('uf')['desmatamento_km2'].sum()
growth_dict = {r['uf']: r['crescimento_pct'] for _, r in df_growth.iterrows()}

scatter_data = []
for uf in desmat_acum.index:
    if uf in growth_dict:
        scatter_data.append({
            'uf': uf,
            'desmat_acum_mil': desmat_acum[uf] / 1000,
            'crescimento': growth_dict[uf],
        })

df_scatter = pd.DataFrame(scatter_data)
colors_sc = [PAL['red'] if c > 50 else PAL['amber'] if c > 0 else PAL['green']
             for c in df_scatter['crescimento']]

ax.scatter(df_scatter['desmat_acum_mil'], df_scatter['crescimento'],
           s=150, c=colors_sc, edgecolors='white', linewidths=2, zorder=5)

for _, row in df_scatter.iterrows():
    ax.annotate(row['uf'], (row['desmat_acum_mil'], row['crescimento']),
                textcoords="offset points", xytext=(8, 5),
                fontsize=12, fontweight='bold', color=PAL['text'])

# Trend line
z = np.polyfit(df_scatter['desmat_acum_mil'], df_scatter['crescimento'], 1)
p = np.poly1d(z)
x_line = np.linspace(df_scatter['desmat_acum_mil'].min(), df_scatter['desmat_acum_mil'].max(), 100)
ax.plot(x_line, p(x_line), '--', color=PAL['muted'], alpha=0.5, linewidth=1.5)

# Correlação
corr = df_scatter['desmat_acum_mil'].corr(df_scatter['crescimento'])
ax.text(0.02, 0.98, f'r = {corr:.2f}', transform=ax.transAxes, fontsize=12,
        fontweight='bold', va='top', color=PAL['dark'],
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.set_xlabel("Desmatamento Acumulado (mil km²)", fontsize=12)
ax.set_ylabel("Crescimento do Rebanho (%)", fontsize=12)
ax.set_title("Desmatamento vs Crescimento do Rebanho — Amazônia Legal", pad=15)
clean_ax(ax)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "04_desmatamento_vs_rebanho.png")
plt.close()
print(f"✅ 04 — Desmatamento vs Rebanho (r = {corr:.2f})")

# %% [markdown]
# ## Gráfico 5 — Taxa de Abate (Proxy de Produtividade)

# %%
fig, ax = plt.subplots(figsize=(13, 6.5))

for regiao, color in REG_COLORS.items():
    sub = df[df['regiao'] == regiao].groupby('ano')['taxa_abate'].mean()
    ax.plot(sub.index, sub.values, color=color, linewidth=2, label=regiao, marker='o', markersize=4)

ax.set_xlabel("Ano", fontsize=12)
ax.set_ylabel("Taxa de Abate (%)", fontsize=12)
ax.set_title("Evolução da Taxa de Abate por Região (Proxy de Intensificação)", pad=15)
ax.legend(loc='best', fontsize=10)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
clean_ax(ax)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "05_taxa_abate.png")
plt.close()
print("✅ 05 — Taxa de abate")

# %% [markdown]
# ## Gráfico 6 — Evolução do Desmatamento na Amazônia Legal

# %%
fig, ax = plt.subplots(figsize=(13, 6))

total_desmat = df[df['amazonia_legal'] == True].groupby('ano')['desmatamento_km2'].sum()
colors = [PAL['red'] if v > 15000 else PAL['amber'] if v > 10000 else PAL['green']
          for v in total_desmat]

ax.bar(total_desmat.index, total_desmat.values / 1000, color=colors, edgecolor='white', width=0.7)
ax.set_xlabel("Ano", fontsize=12)
ax.set_ylabel("Desmatamento (mil km²)", fontsize=12)
ax.set_title("Desmatamento Anual na Amazônia Legal (INPE/PRODES)", pad=15)

# Anotar picos
max_year = total_desmat.idxmax()
ax.annotate(f'Pico: {total_desmat[max_year]/1000:.1f}k km²',
            xy=(max_year, total_desmat[max_year]/1000),
            xytext=(max_year+2, total_desmat[max_year]/1000 + 2),
            arrowprops=dict(arrowstyle='->', color=PAL['red']),
            fontsize=11, fontweight='bold', color=PAL['red'])

clean_ax(ax)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "06_desmatamento_temporal.png")
plt.close()
print("✅ 06 — Desmatamento temporal")

# %% [markdown]
# ## Gráfico 7 — Correlação entre Variáveis

# %%
fig, ax = plt.subplots(figsize=(9, 7))

amz_full = df[df['amazonia_legal'] == True].dropna(subset=['desmatamento_km2'])
cols = ['rebanho_cabecas', 'abate_anual', 'desmatamento_km2', 'taxa_abate', 'var_rebanho_pct']
labels = ['Rebanho', 'Abate', 'Desmatamento', 'Taxa Abate', 'Var. Rebanho']

corr = amz_full[cols].corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
cmap = sns.diverging_palette(220, 130, as_cmap=True)

sns.heatmap(corr, mask=mask, cmap=cmap, center=0,
            annot=True, fmt='.2f', linewidths=0.5,
            xticklabels=labels, yticklabels=labels,
            square=True, ax=ax, cbar_kws={'shrink': 0.8},
            annot_kws={'fontsize': 11})
ax.set_title("Correlação — Amazônia Legal", pad=15, fontsize=15)
plt.tight_layout()
fig.savefig(PLOTS_PATH / "07_correlacao.png")
plt.close()
print("✅ 07 — Correlação")

print("\n" + "=" * 50)
print("✅ EDA CONCLUÍDA! 7 gráficos gerados.")
