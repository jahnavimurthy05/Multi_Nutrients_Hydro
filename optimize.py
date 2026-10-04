# optimize.py
# Usage: python optimize.py Tomato,Lettuce,Spinach
import sys, json
import random, math
import matplotlib.pyplot as plt
from deap import base, creator, tools, algorithms
import numpy as np

# --- Crop database (same as you had) ---
crop_db = {
    "Tomato":    {"pH": 6.0, "EC": 2.0, "N": 250, "P": 50, "K": 300, "yield_factor": 1.2},
    "Lettuce":   {"pH": 6.2, "EC": 1.2, "N": 180, "P": 40, "K": 200, "yield_factor": 1.0},
    "Spinach":   {"pH": 6.0, "EC": 1.8, "N": 200, "P": 60, "K": 220, "yield_factor": 1.1},
    "Cucumber":  {"pH": 5.8, "EC": 1.7, "N": 220, "P": 55, "K": 250, "yield_factor": 1.3},
    "Strawberry":{"pH": 6.0, "EC": 1.4, "N": 160, "P": 50, "K": 180, "yield_factor": 1.0},
    "Basil":     {"pH": 6.2, "EC": 1.5, "N": 190, "P": 45, "K": 160, "yield_factor": 0.9},
    "Beans":     {"pH": 6.0, "EC": 2.2, "N": 200, "P": 50, "K": 250, "yield_factor": 1.1},
    "Carrot":    {"pH": 6.3, "EC": 1.6, "N": 180, "P": 45, "K": 210, "yield_factor": 0.8},
    "Peas":      {"pH": 6.0, "EC": 1.8, "N": 190, "P": 50, "K": 220, "yield_factor": 1.0},
    "Cabbage":   {"pH": 6.5, "EC": 2.0, "N": 230, "P": 55, "K": 300, "yield_factor": 1.2},
    "Okra":      {"pH": 6.0, "EC": 2.0, "N": 240, "P": 50, "K": 280, "yield_factor": 1.3},
    "Mint":      {"pH": 6.0, "EC": 1.2, "N": 150, "P": 35, "K": 150, "yield_factor": 0.8},
    "Microgreens":{"pH": 6.0, "EC": 0.8, "N": 100, "P": 30, "K": 100, "yield_factor": 0.7}
}

# parse crops from argv (comma separated) or default to all
arg = sys.argv[1] if len(sys.argv) > 1 else ""
selected = [c.strip() for c in arg.split(",") if c.strip() in crop_db] if arg else list(crop_db.keys())
if not selected:
    print(json.dumps({"error":"No valid crops selected"}))
    sys.exit(1)
crops = {k: crop_db[k] for k in selected}

# nutrient interaction penalty (kept as in your code)
def nutrient_interaction_penalty(N, P, K, EC):
    ideal_ratio = (4, 1, 3)
    total = N + P + K
    if total == 0:
        return 1000
    n_ratio = (N / total) / (ideal_ratio[0] / sum(ideal_ratio)) if sum(ideal_ratio) > 0 else 0
    p_ratio = (P / total) / (ideal_ratio[1] / sum(ideal_ratio)) if sum(ideal_ratio) > 0 else 0
    k_ratio = (K / total) / (ideal_ratio[2] / sum(ideal_ratio)) if sum(ideal_ratio) > 0 else 0
    ratio_penalty = abs(1 - n_ratio) + abs(1 - p_ratio) + abs(1 - k_ratio)
    ec_penalty = 0
    if EC > 2.5:
        ec_penalty = (EC - 2.5) * 2
    elif EC < 1.0:
        ec_penalty = (1.0 - EC)
    return ratio_penalty + ec_penalty

def evaluate(ind):
    pH, EC, N, P, K = ind
    score = 0
    for crop, vals in crops.items():
        yield_factor = vals.get("yield_factor", 1.0)
        diff = (
            abs(pH - vals["pH"]) +
            abs(EC - vals["EC"]) +
            abs(N - vals["N"]) / 50 +
            abs(P - vals["P"]) / 20 +
            abs(K - vals["K"]) / 50
        )
        interaction_penalty = nutrient_interaction_penalty(N, P, K, EC)
        score += (diff + interaction_penalty) * yield_factor
    return (score,)

# Setup DEAP
creator = base.Creator if hasattr(base, "Creator") else None
# Clean creators if they exist
try:
    del creator
except:
    pass

from deap import creator as _creator
# ensure no duplicate names
for name in ("FitnessMin","Individual"):
    if name in _creator.__dict__:
        del _creator.__dict__[name]

_creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
_creator.create("Individual", list, fitness=_creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("attr_pH", random.uniform, 5.5, 6.5)
toolbox.register("attr_EC", random.uniform, 1.0, 2.5)
toolbox.register("attr_N", random.uniform, 150, 300)
toolbox.register("attr_P", random.uniform, 30, 80)
toolbox.register("attr_K", random.uniform, 150, 350)
toolbox.register("individual", tools.initCycle, _creator.Individual,
                 (toolbox.attr_pH, toolbox.attr_EC, toolbox.attr_N, toolbox.attr_P, toolbox.attr_K), n=1)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("mate", tools.cxBlend, alpha=0.5)
# mutGaussian with scalar sigma uses numbers not lists -> use lambda mutate wrapper
def mutate_gauss(individual, mu, sigma, indpb):
    for i in range(len(individual)):
        if random.random() < indpb:
            individual[i] += random.gauss(mu[i], sigma[i])
    return individual,
toolbox.register("mutate", mutate_gauss, mu=[0,0,0,0,0], sigma=[0.1,0.1,10,5,10], indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate)

# Bound checking decorator
def check_bounds(mins, maxs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            offspring = func(*args, **kwargs)
            for child in offspring:
                for i in range(len(child)):
                    if child[i] < mins[i]:
                        child[i] = mins[i]
                    elif child[i] > maxs[i]:
                        child[i] = maxs[i]
            return offspring
        return wrapper
    return decorator

bounds = ([5.5, 1.0, 150, 30, 150], [6.5, 2.5, 300, 80, 350])
toolbox.decorate("mate", check_bounds(*bounds))
toolbox.decorate("mutate", check_bounds(*bounds))

# statistics
stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", np.mean)
stats.register("min", np.min)
stats.register("max", np.max)

# run GA
pop = toolbox.population(n=120)
logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.7, mutpb=0.4, ngen=120, stats=stats, verbose=False)
best = tools.selBest(pop, 1)[0]

# Prepare results
best_vals = [round(x,2) for x in best]
deviations = {}
for crop, vals in crops.items():
    deviations[crop] = {
        "pH": round(best[0] - vals["pH"], 2),
        "EC": round(best[1] - vals["EC"], 2),
        "N": round(best[2] - vals["N"], 1),
        "P": round(best[3] - vals["P"], 1),
        "K": round(best[4] - vals["K"], 1)
    }

# Plot nutrient balance and save to public/optimize_plot.png
def plot_nutrient_balance(N, P, K, EC, outpath):
    ideal = [4,1,3]
    current = [N, P, K]
    total = sum(current)
    ideal_total = sum(ideal)
    current_norm = [x/total if total>0 else 0 for x in current]
    ideal_norm = [x/ideal_total if ideal_total>0 else 0 for x in ideal]

    fig, ax = plt.subplots(figsize=(6,4))
    labels = ['N','P','K']
    x = np.arange(len(labels))
    ax.bar(x - 0.15, ideal_norm, width=0.3, label='Ideal Ratio', color='lightgreen')
    ax.bar(x + 0.15, current_norm, width=0.3, label='Optimized Ratio', color='teal')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Relative Proportion')
    ax.set_title(f'Nutrient Balance (EC={round(EC,2)})')
    ax.legend()
    plt.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)

import os
outplot = "optimize_plot.png"
plot_nutrient_balance(best[2], best[3], best[4], best[1], outplot)
if os.path.exists("public"):
    plot_nutrient_balance(best[2], best[3], best[4], best[1], os.path.join("public", "optimize_plot.png"))

result = {
    "best": {
        "pH": round(best[0],2),
        "EC": round(best[1],2),
        "N": round(best[2],1),
        "P": round(best[3],1),
        "K": round(best[4],1)
    },
    "deviations": deviations,
    "plot": "/optimize_plot.png",
    "selected_crops": selected
}

# print JSON to stdout for Node to read
print(json.dumps(result))
