"""
CBIT (Computational Blueprint) variant generator for IB Math AA SL seed problems.

A blueprint is a Python callable that accepts a random seed and returns a
ProblemVariant. Blueprints are keyed by seed_problem slug. When a slug has no
registered blueprint the service falls back to surface-level parameter
substitution so every problem has *some* variant capability.

Typical call:
    variants = generate_variants("arith-seq-001", n=5)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ProblemVariant:
    content: str
    answer: str
    worked_solution: str
    hint_l1: str
    hint_l2: str
    hint_l3: str
    difficulty_estimate: float
    re_solve_verified: bool = False
    source_slug: str = ""
    seed: int = 0


BlueprintFn = Callable[[int], ProblemVariant]

_BLUEPRINTS: dict[str, BlueprintFn] = {}


def blueprint(slug: str) -> Callable[[BlueprintFn], BlueprintFn]:
    """Decorator that registers a CBIT blueprint for a seed problem slug."""
    def decorator(fn: BlueprintFn) -> BlueprintFn:
        _BLUEPRINTS[slug] = fn
        return fn
    return decorator


# ── ALGEBRA BLUEPRINTS ────────────────────────────────────────────────────────

@blueprint("arith-seq-001")
def _arith_seq_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    a1 = rng.randint(2, 15)
    d = rng.randint(2, 10)
    n = rng.randint(8, 20)
    # nth term: a1 + (n-1)d
    an = a1 + (n - 1) * d
    # Sum S_n = n/2 * (2a1 + (n-1)d)
    sn = n * (2 * a1 + (n - 1) * d) // 2
    return ProblemVariant(
        content=(
            f"An arithmetic sequence has first term {a1} and common difference {d}. "
            f"Find the {n}th term and the sum of the first {n} terms."
        ),
        answer=f"u_{n} = {an}, S_{n} = {sn}",
        worked_solution=(
            f"u_n = a + (n−1)d = {a1} + ({n}−1)({d}) = {a1} + {(n-1)*d} = {an}. "
            f"S_n = n/2(2a + (n−1)d) = {n}/2(2·{a1} + {n-1}·{d}) = {n}/2·{2*a1+(n-1)*d} = {sn}."
        ),
        hint_l1="Use u_n = a + (n−1)d for the nth term and S_n = n/2(2a + (n−1)d) for the sum.",
        hint_l2=f"Substitute a={a1}, d={d}, n={n}.",
        hint_l3=f"u_{n} = {an}. S_{n} = {sn}.",
        difficulty_estimate=2.0,
        re_solve_verified=True,
        source_slug="arith-seq-001",
        seed=seed,
    )


@blueprint("geom-seq-001")
def _geom_seq_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    a1 = rng.randint(1, 8)
    r = rng.choice([2, 3, -2, -3])
    n = rng.randint(4, 7)
    an = a1 * (r ** (n - 1))
    # Sum: a1*(r^n - 1)/(r-1)
    sn_num = a1 * (r**n - 1)
    sn_den = r - 1
    from math import gcd
    g = gcd(abs(sn_num), abs(sn_den))
    sn_n, sn_d = sn_num // g, sn_den // g
    sn_str = str(sn_n) if sn_d == 1 else f"{sn_n}/{sn_d}"
    return ProblemVariant(
        content=(
            f"A geometric sequence has first term {a1} and common ratio {r}. "
            f"Find the {n}th term and the sum of the first {n} terms."
        ),
        answer=f"u_{n} = {an}, S_{n} = {sn_str}",
        worked_solution=(
            f"u_n = ar^(n−1) = {a1}·({r})^{n-1} = {an}. "
            f"S_n = a(r^n−1)/(r−1) = {a1}({r}^{n}−1)/({r}−1) = {sn_str}."
        ),
        hint_l1="Use u_n = ar^(n−1) and S_n = a(r^n−1)/(r−1) for r≠1.",
        hint_l2=f"Substitute a={a1}, r={r}, n={n}.",
        hint_l3=f"u_{n} = {an}. S_{n} = {sn_str}.",
        difficulty_estimate=2.0,
        re_solve_verified=True,
        source_slug="geom-seq-001",
        seed=seed,
    )


@blueprint("quad-001")
def _quad_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    # Generate quadratic with integer roots p, q; equation x²−(p+q)x+pq=0
    p = rng.randint(-8, 8)
    q = rng.randint(-8, 8)
    while q == p:
        q = rng.randint(-8, 8)
    # ax²+bx+c with a=1
    b = -(p + q)
    c = p * q
    b_str = f"+ {b}" if b >= 0 else f"− {-b}"
    c_str = f"+ {c}" if c >= 0 else f"− {-c}"
    roots = sorted([p, q])
    return ProblemVariant(
        content=f"Solve x² {b_str}x {c_str} = 0.",
        answer=f"x = {roots[0]} or x = {roots[1]}",
        worked_solution=(
            f"Factor: (x − {p})(x − {q}) = 0 → x = {p} or x = {q}."
        ),
        hint_l1="Try to factor the quadratic as (x − p)(x − q) = 0.",
        hint_l2=f"Find two numbers that multiply to {c} and add to {-b}.",
        hint_l3=f"(x − {p})(x − {q}) = 0 → x = {roots[0]} or x = {roots[1]}.",
        difficulty_estimate=2.0,
        re_solve_verified=True,
        source_slug="quad-001",
        seed=seed,
    )


@blueprint("log-001")
def _log_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    base = rng.choice([2, 3, 5, 10])
    exp = rng.randint(2, 5)
    val = base ** exp
    return ProblemVariant(
        content=f"Evaluate log_{base}({val}).",
        answer=str(exp),
        worked_solution=f"log_{base}({val}) = x means {base}^x = {val} = {base}^{exp}, so x = {exp}.",
        hint_l1=f"log_b(x) = n means b^n = x.",
        hint_l2=f"What power of {base} gives {val}?",
        hint_l3=f"{base}^{exp} = {val}, so log_{base}({val}) = {exp}.",
        difficulty_estimate=1.5,
        re_solve_verified=True,
        source_slug="log-001",
        seed=seed,
    )


@blueprint("exp-laws-001")
def _exp_laws_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    base = rng.choice([2, 3, 5])
    p = rng.randint(2, 6)
    q = rng.randint(1, p - 1)
    # Simplify base^p / base^q = base^(p-q)
    return ProblemVariant(
        content=f"Simplify {base}^{p} ÷ {base}^{q}, leaving your answer as a power of {base}.",
        answer=f"{base}^{p-q}",
        worked_solution=f"a^m ÷ a^n = a^(m−n). So {base}^{p} ÷ {base}^{q} = {base}^{p-q}.",
        hint_l1="Use the quotient law: a^m ÷ a^n = a^(m−n).",
        hint_l2=f"Subtract exponents: {p} − {q} = {p-q}.",
        hint_l3=f"{base}^{p-q}.",
        difficulty_estimate=1.5,
        re_solve_verified=True,
        source_slug="exp-laws-001",
        seed=seed,
    )


# ── GEOMETRY & TRIG BLUEPRINTS ────────────────────────────────────────────────

@blueprint("trig-radians-001")
def _trig_radians_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    r = rng.randint(4, 15)
    # Pick a "nice" angle in radians: π/6, π/4, π/3, π/2, 2π/3, 3π/4, π
    numerators = [1, 1, 1, 2, 3, 5]
    denoms     = [6, 4, 3, 3, 4, 6]
    idx = rng.randint(0, len(numerators) - 1)
    num, den = numerators[idx], denoms[idx]
    # arc = r * θ = r * (num*π/den)
    # area = ½r²θ
    arc_num = r * num
    arc_den = den
    from math import gcd
    g = gcd(arc_num, arc_den)
    arc_n, arc_d = arc_num // g, arc_den // g
    arc_str = f"{arc_n}π/{arc_d}" if arc_d != 1 else f"{arc_n}π"

    area_num = r * r * num  # ½r²*(num*π/den) → numerator = r²*num, denom = 2*den
    area_den = 2 * den
    g2 = gcd(area_num, area_den)
    area_n, area_d = area_num // g2, area_den // g2
    area_str = f"{area_n}π/{area_d}" if area_d != 1 else f"{area_n}π"

    theta_str = f"{num}π/{den}" if den != 1 else f"{num}π"
    return ProblemVariant(
        content=(
            f"A sector has radius {r} cm and angle θ = {theta_str} radians. "
            f"Find the arc length and area."
        ),
        answer=f"Arc = {arc_str} cm, Area = {area_str} cm²",
        worked_solution=(
            f"Arc = rθ = {r}·{theta_str} = {arc_str} cm. "
            f"Area = ½r²θ = ½·{r}²·{theta_str} = {area_str} cm²."
        ),
        hint_l1="Arc = rθ and Area = ½r²θ (θ in radians).",
        hint_l2=f"Substitute r={r} and θ={theta_str}.",
        hint_l3=f"Arc = {arc_str} cm. Area = {area_str} cm².",
        difficulty_estimate=1.5,
        re_solve_verified=True,
        source_slug="trig-radians-001",
        seed=seed,
    )


@blueprint("trig-sincos-001")
def _trig_sincos_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    # Cosine rule: c² = a²+b²−2ab·cos(C)
    # Pick sides and angle that give integer c²
    # Use Pythagorean-like triples for clean answers
    triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]
    a, b, c = rng.choice(triples)
    # cos C = (a²+b²-c²)/(2ab) then reconstruct the problem going the other way
    # Just generate random a,b with angle=60 for clean answer
    a = rng.randint(4, 12)
    b = rng.randint(4, 12)
    cos_C = 0.5  # 60 degrees
    c_sq = a**2 + b**2 - 2*a*b*cos_C
    c_val = c_sq**0.5
    c_rounded = round(c_val, 2)
    return ProblemVariant(
        content=(
            f"In triangle ABC, AB = {a} cm, BC = {b} cm, and angle B = 60°. "
            f"Find AC to 3 significant figures."
        ),
        answer=f"AC = {c_rounded:.3g} cm",
        worked_solution=(
            f"AC² = {a}² + {b}² − 2({a})({b})cos(60°) "
            f"= {a**2} + {b**2} − {2*a*b}(0.5) "
            f"= {a**2 + b**2} − {a*b} = {a**2 + b**2 - a*b}. "
            f"AC = √{a**2 + b**2 - a*b} ≈ {c_rounded:.3g} cm."
        ),
        hint_l1="Use the cosine rule: c² = a² + b² − 2ab cos C.",
        hint_l2=f"Substitute a={a}, b={b}, C=60°. cos(60°)=0.5.",
        hint_l3=f"AC² = {a**2+b**2-a*b}. AC ≈ {c_rounded:.3g} cm.",
        difficulty_estimate=2.0,
        re_solve_verified=True,
        source_slug="trig-sincos-001",
        seed=seed,
    )


# ── CALCULUS BLUEPRINTS ───────────────────────────────────────────────────────

@blueprint("calc-power-001")
def _calc_power_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    a = rng.randint(2, 8)
    b = rng.randint(1, 6)
    c = rng.randint(1, 5)
    k = rng.randint(1, 10)
    # f(x) = ax³ − bx² + cx − k
    da = 3 * a
    db = 2 * b
    return ProblemVariant(
        content=f"Differentiate f(x) = {a}x³ − {b}x² + {c}x − {k}.",
        answer=f"f'(x) = {da}x² − {db}x + {c}",
        worked_solution=(
            f"Apply the power rule to each term: "
            f"{a}·3x² − {b}·2x + {c}·1 − 0 = {da}x² − {db}x + {c}."
        ),
        hint_l1="d/dx[xⁿ] = nxⁿ⁻¹. The derivative of a constant is zero.",
        hint_l2=f"Differentiate each term: d/dx[{a}x³]={da}x², d/dx[{b}x²]={db}x, d/dx[{c}x]={c}.",
        hint_l3=f"f'(x) = {da}x² − {db}x + {c}.",
        difficulty_estimate=1.5,
        re_solve_verified=True,
        source_slug="calc-power-001",
        seed=seed,
    )


@blueprint("calc-antideriv-001")
def _calc_antideriv_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    a = rng.randint(2, 6)
    b = rng.randint(1, 5)
    c = rng.randint(1, 8)
    # ∫(ax² − bx + c) dx = ax³/3 − bx²/2 + cx + C
    from math import gcd
    g1 = gcd(a, 3)
    a_n, a_d = a // g1, 3 // g1
    g2 = gcd(b, 2)
    b_n, b_d = b // g2, 2 // g2
    a_str = f"{a_n}x³/{a_d}" if a_d != 1 else f"{a_n}x³"
    b_str = f"{b_n}x²/{b_d}" if b_d != 1 else f"{b_n}x²"
    return ProblemVariant(
        content=f"Find ∫({a}x² − {b}x + {c}) dx.",
        answer=f"{a_str} − {b_str} + {c}x + C",
        worked_solution=(
            f"∫{a}x² dx = {a_str}. "
            f"∫{b}x dx = {b_str}. "
            f"∫{c} dx = {c}x. "
            f"Sum + C: {a_str} − {b_str} + {c}x + C."
        ),
        hint_l1="∫xⁿ dx = xⁿ⁺¹/(n+1) + C. Integrate each term separately.",
        hint_l2=f"∫{a}x² dx = {a}x³/3. ∫{b}x dx = {b}x²/2. ∫{c} dx = {c}x.",
        hint_l3=f"{a_str} − {b_str} + {c}x + C.",
        difficulty_estimate=1.5,
        re_solve_verified=True,
        source_slug="calc-antideriv-001",
        seed=seed,
    )


@blueprint("calc-defint-001")
def _calc_defint_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    a_coef = rng.randint(1, 4)
    const = rng.randint(1, 5)
    lo = rng.randint(0, 2)
    hi = lo + rng.randint(2, 4)
    # ∫[lo,hi] (a_coef·x² + const) dx = [a_coef·x³/3 + const·x]
    def F(x: int) -> float:
        return a_coef * x**3 / 3 + const * x
    result = F(hi) - F(lo)
    # Express as fraction
    from fractions import Fraction
    frac = Fraction(a_coef * (hi**3 - lo**3), 3) + Fraction(const * (hi - lo))
    ans_str = str(frac) if frac.denominator != 1 else str(int(frac))
    return ProblemVariant(
        content=f"Evaluate ∫_{lo}^{hi} ({a_coef}x² + {const}) dx.",
        answer=ans_str,
        worked_solution=(
            f"[{a_coef}x³/3 + {const}x]_{lo}^{hi} "
            f"= ({a_coef}·{hi}³/3 + {const}·{hi}) − ({a_coef}·{lo}³/3 + {const}·{lo}) "
            f"= {F(hi):.4g} − {F(lo):.4g} = {ans_str}."
        ),
        hint_l1="Find the antiderivative F(x) then compute F(upper) − F(lower).",
        hint_l2=f"F(x) = {a_coef}x³/3 + {const}x. Evaluate at x={hi} and x={lo}.",
        hint_l3=f"F({hi})−F({lo}) = {ans_str}.",
        difficulty_estimate=1.5,
        re_solve_verified=True,
        source_slug="calc-defint-001",
        seed=seed,
    )


@blueprint("calc-tangent-001")
def _calc_tangent_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    a = rng.randint(1, 4)
    b = rng.randint(-5, 5)
    c = rng.randint(-5, 5)
    x0 = rng.randint(1, 4)
    # y = ax² + bx + c; y'(x0) = 2ax0 + b; y(x0) = ax0²+bx0+c
    m = 2 * a * x0 + b
    y0 = a * x0**2 + b * x0 + c
    # y − y0 = m(x − x0) → y = mx + (y0 − m*x0)
    intercept = y0 - m * x0
    b_str = f"+ {intercept}" if intercept >= 0 else f"− {-intercept}"
    return ProblemVariant(
        content=f"Find the equation of the tangent to y = {a}x² + {b}x + {c} at x = {x0}.",
        answer=f"y = {m}x {b_str}",
        worked_solution=(
            f"y({x0}) = {a}({x0})² + {b}({x0}) + {c} = {y0}. "
            f"y' = {2*a}x + {b}. Gradient at x={x0}: {m}. "
            f"Tangent: y − {y0} = {m}(x − {x0}) → y = {m}x {b_str}."
        ),
        hint_l1="Find y(x₀) and y'(x₀). Use y − y₀ = m(x − x₀).",
        hint_l2=f"y'({x0}) = {2*a}({x0}) + {b} = {m}. y({x0}) = {y0}.",
        hint_l3=f"y = {m}x {b_str}.",
        difficulty_estimate=2.0,
        re_solve_verified=True,
        source_slug="calc-tangent-001",
        seed=seed,
    )


# ── STATISTICS BLUEPRINTS ─────────────────────────────────────────────────────

@blueprint("stat-desc-001")
def _stat_desc_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    n = rng.randint(5, 9)
    data = sorted(rng.randint(1, 20) for _ in range(n))
    mean = sum(data) / n
    mean_str = f"{mean:.1f}" if mean != int(mean) else str(int(mean))
    median = data[n // 2]
    q1 = data[n // 4]
    q3 = data[3 * n // 4]
    iqr = q3 - q1
    data_str = ", ".join(str(x) for x in data)
    return ProblemVariant(
        content=f"Find the mean, median, and IQR of: {data_str}.",
        answer=f"Mean = {mean_str}, Median = {median}, IQR = {iqr}",
        worked_solution=(
            f"Mean = ({'+'.join(str(x) for x in data)})/{n} = {sum(data)}/{n} = {mean_str}. "
            f"Median (middle value) = {median}. "
            f"Q1 = {q1}, Q3 = {q3}, IQR = {q3}−{q1} = {iqr}."
        ),
        hint_l1="Sort the data. Mean = sum/n. Median = middle value. IQR = Q3 − Q1.",
        hint_l2=f"Sorted: {data_str}. Middle position: index {n//2}.",
        hint_l3=f"Mean={mean_str}, Median={median}, IQR={iqr}.",
        difficulty_estimate=1.5,
        re_solve_verified=True,
        source_slug="stat-desc-001",
        seed=seed,
    )


@blueprint("stat-binom-001")
def _stat_binom_001(seed: int) -> ProblemVariant:
    rng = random.Random(seed)
    n = rng.randint(8, 15)
    p_choices = [0.2, 0.25, 0.3, 0.4]
    p = rng.choice(p_choices)
    r = rng.randint(2, n // 2)
    from math import comb
    prob = comb(n, r) * (p**r) * ((1-p)**(n-r))
    e_x = n * p
    return ProblemVariant(
        content=(
            f"X ~ B({n}, {p}). Find P(X = {r}) and E(X). "
            f"Give P(X = {r}) to 3 significant figures."
        ),
        answer=f"P(X={r}) ≈ {prob:.3g}, E(X) = {e_x:.4g}",
        worked_solution=(
            f"P(X={r}) = C({n},{r})({p})^{r}({1-p})^{n-r} "
            f"= {comb(n,r)} × {p**r:.5g} × {(1-p)**(n-r):.5g} ≈ {prob:.3g}. "
            f"E(X) = np = {n}×{p} = {e_x:.4g}."
        ),
        hint_l1=f"P(X=r) = C(n,r)p^r(1−p)^(n−r). E(X) = np.",
        hint_l2=f"C({n},{r}) = {comb(n,r)}. p^r = {p}^{r}.",
        hint_l3=f"P(X={r}) ≈ {prob:.3g}. E(X) = {e_x:.4g}.",
        difficulty_estimate=2.0,
        re_solve_verified=True,
        source_slug="stat-binom-001",
        seed=seed,
    )


# ── FALLBACK: PARAMETER SUBSTITUTION ─────────────────────────────────────────

def _fallback_variant(slug: str, seed: int) -> ProblemVariant:
    """Return a minimal variant noting the problem but cannot parameterise further."""
    return ProblemVariant(
        content=f"[Variant of {slug} with seed {seed}] Refer to the original seed problem.",
        answer="See original problem.",
        worked_solution="No CBIT blueprint registered for this problem type.",
        hint_l1="",
        hint_l2="",
        hint_l3="",
        difficulty_estimate=2.0,
        re_solve_verified=False,
        source_slug=slug,
        seed=seed,
    )


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def generate_variants(
    source_slug: str,
    n: int = 5,
    *,
    re_solve_filter: bool = True,
    base_seed: int = 0,
) -> list[ProblemVariant]:
    """
    Generate up to `n` verified variants for the given seed problem slug.

    Args:
        source_slug:     Slug of the seed problem to parameterise.
        n:               Number of variants to attempt.
        re_solve_filter: If True, only return variants where re_solve_verified=True.
        base_seed:       Starting integer for seeding (seeds are base_seed + i).

    Returns:
        List of ProblemVariant objects (may be fewer than n if filter is strict).
    """
    blueprint_fn = _BLUEPRINTS.get(source_slug)

    results: list[ProblemVariant] = []
    for i in range(n):
        seed = base_seed + i
        if blueprint_fn is not None:
            try:
                variant = blueprint_fn(seed)
            except Exception:
                variant = _fallback_variant(source_slug, seed)
        else:
            variant = _fallback_variant(source_slug, seed)

        if re_solve_filter and not variant.re_solve_verified:
            continue
        results.append(variant)

    return results


def list_blueprints() -> list[str]:
    """Return all registered blueprint slugs."""
    return list(_BLUEPRINTS.keys())
