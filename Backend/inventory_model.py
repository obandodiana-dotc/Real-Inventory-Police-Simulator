from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

DAYS_PER_YEAR = 365

# Simplified table of Z-values for different service levels
Z_TABLE = {
    0.80: 0.842,
    0.81: 0.878,
    0.82: 0.915,
    0.83: 0.954,
    0.84: 0.994,
    0.85: 1.036,
    0.86: 1.080,
    0.87: 1.126,
    0.88: 1.175,
    0.89: 1.227,
    0.90: 1.282,
    0.91: 1.341,
    0.92: 1.405,
    0.93: 1.476,
    0.94: 1.555,
    0.95: 1.645,
    0.96: 1.751,
    0.97: 1.880,
    0.98: 2.054,
    0.99: 2.326,
    0.995: 2.576,
    0.999: 3.090,
}


def z_from_service(service: float) -> float:
    """
    Approximate z-value for a given service level using the
    Z_TABLE and linear interpolation.
    """
    if service in Z_TABLE:
        return Z_TABLE[service]
    keys = sorted(Z_TABLE.keys())
    if service <= keys[0]:
        return Z_TABLE[keys[0]]
    if service >= keys[-1]:
        return Z_TABLE[keys[-1]]
    for lo, hi in zip(keys, keys[1:]):
        if lo <= service <= hi:
            z_lo, z_hi = Z_TABLE[lo], Z_TABLE[hi]
            ratio = (service - lo) / (hi - lo)
            return z_lo + ratio * (z_hi - z_lo)
    # fallback around 95%
    return 1.645


@dataclass
class SkuConfig:
    sku_id: str
    name: str
    annual_demand: float
    demand_std_pct: float
    lead_time_days: int
    lead_time_std_pct: float
    unit_cost: float
    holding_cost_pct: float
    order_cost_fixed: float
    stockout_cost_per_unit: float
    policy_type: str
    # optional policy parameters (if user overwrites defaults)
    reorder_point: Optional[float] = None
    order_qty: Optional[float] = None
    min_inv: Optional[float] = None
    max_inv: Optional[float] = None
    review_period_days: Optional[int] = None
    # seasonality & trend
    seasonality_enabled: bool = True
    seasonality_amplitude: float = 0.2
    trend_pct_per_year: float = 0.0


@dataclass
class DailyState:
    day: int
    on_hand: float
    on_order: float
    demand: float
    shipped: float
    stockout: bool


@dataclass
class SkuResult:
    sku_id: str
    name: str
    policy_type: str
    total_demand: float
    filled_demand: float
    fill_rate_pct: float
    avg_inventory: float
    avg_inventory_value: float
    unit_cost: float
    stockout_days: int
    num_orders: int
    total_cost: float
    holding_cost: float
    ordering_cost: float
    stockout_cost: float
    daily_states: List[DailyState]


def seasonal_multiplier(day: int, amplitude: float, trend_pct_per_year: float) -> float:
    """Seasonal + trend multiplier for demand."""
    season = 1.0 + amplitude * math.sin(2 * math.pi / 365.0 * day)
    trend = (1.0 + trend_pct_per_year) ** (day / 365.0)
    return season * trend


def draw_daily_demand(cfg: SkuConfig, day: int, rng: random.Random) -> float:
    """Draw daily demand with seasonality and normal variation."""
    base_daily = cfg.annual_demand / DAYS_PER_YEAR
    mult = 1.0
    if cfg.seasonality_enabled:
                mult = seasonal_multiplier(day, cfg.seasonality_amplitude, cfg.trend_pct_per_year)
    mean = base_daily * mult
    std = mean * cfg.demand_std_pct
    d = rng.gauss(mean, std)
    return max(0.0, d)


def draw_lead_time(cfg: SkuConfig, rng: random.Random) -> int:
    """Random lead time (Gaussian, truncated at >= 1 day)."""
    mean = cfg.lead_time_days
    std = max(0.1, mean * cfg.lead_time_std_pct)
    lt = rng.gauss(mean, std)
    return max(1, int(round(lt)))


def compute_policy(cfg: SkuConfig, service_level: float) -> None:
    """
    Compute reorder_point, order_qty, min/max, etc. based on policy_type
    and target service level.
    """
    z = z_from_service(service_level)
    daily = cfg.annual_demand / DAYS_PER_YEAR
    daily_std = daily * cfg.demand_std_pct
    pt = cfg.policy_type.upper()

    if pt == "EOQ":
        h_year = cfg.unit_cost * cfg.holding_cost_pct
        if h_year <= 0:
            h_year = cfg.unit_cost * 0.25
        if cfg.order_cost_fixed <= 0:
            cfg.order_cost_fixed = 50.0
        cfg.order_qty = math.sqrt(2 * cfg.annual_demand * cfg.order_cost_fixed / h_year)
        lt = cfg.lead_time_days
        sigma_lt = daily_std * math.sqrt(lt)
        safety = z * sigma_lt
        cfg.reorder_point = daily * lt + safety

    elif pt == "ROP":
        lt = cfg.lead_time_days
        sigma_lt = daily_std * math.sqrt(lt)
        safety = z * sigma_lt
        if not cfg.order_qty or cfg.order_qty <= 0:
            h_year = cfg.unit_cost * cfg.holding_cost_pct or cfg.unit_cost * 0.25
            cfg.order_qty = math.sqrt(
                2 * cfg.annual_demand * max(cfg.order_cost_fixed, 1.0) / h_year
            )
        cfg.reorder_point = daily * lt + safety

    elif pt == "MINMAX":
        lt = cfg.lead_time_days
        sigma_lt = daily_std * math.sqrt(lt)
        safety = z * sigma_lt
        base = daily * lt
        h_year = cfg.unit_cost * cfg.holding_cost_pct or cfg.unit_cost * 0.25
        eoq = math.sqrt(
            2 * cfg.annual_demand * max(cfg.order_cost_fixed, 1.0) / h_year
        )
        cfg.min_inv = base + safety  # Min = punto de reorden
        cfg.max_inv = base + safety + eoq  # Max = punto de reorden + EOQ

    elif pt == "PERIODIC":
        if not cfg.review_period_days or cfg.review_period_days <= 0:
            cfg.review_period_days = max(1, cfg.lead_time_days)
        P = cfg.review_period_days
        L = cfg.lead_time_days
        mean_period = daily * (P + L)
        std_period = daily_std * math.sqrt(P + L)
        target = mean_period + z * std_period
        cfg.max_inv = target

    else:
        # fallback: EOQ
        cfg.policy_type = "EOQ"
        compute_policy(cfg, service_level)


def simulate_single_sku(
    cfg: SkuConfig,
    sim_days: int,
    service_level: float,
    seed: int,
) -> SkuResult:
    """Simulate daily inventory dynamics for a single SKU."""
    rng = random.Random(seed)
    compute_policy(cfg, service_level)
    holding_per_day = cfg.unit_cost * cfg.holding_cost_pct / DAYS_PER_YEAR

    # Initial inventory: one order quantity or max_inv or small buffer
    on_hand = cfg.order_qty or cfg.max_inv or 10.0
    pipeline: List[Tuple[int, float]] = []

    total_dem = filled_dem = 0.0
    stockout_days = num_orders = 0
    sum_inv = 0.0
    holding = ordering = stockout_cost = 0.0
    daily_states: List[DailyState] = []

    for day in range(1, sim_days + 1):
        # 1) Arrivals
        arriving = 0.0
        new_pipe: List[Tuple[int, float]] = []
        for arr, qty in pipeline:
            if arr == day:
                arriving += qty
            else:
                new_pipe.append((arr, qty))
        pipeline = new_pipe
        on_hand += arriving

        # 2) Demand realization
        demand = draw_daily_demand(cfg, day, rng)
        total_dem += demand
        shipped = min(on_hand, demand)
        on_hand -= shipped
        filled_dem += shipped
        stockout = demand > shipped + 1e-6
        if stockout:
            stockout_days += 1
            lost = demand - shipped
            stockout_cost += lost * cfg.stockout_cost_per_unit

        # 3) Policy ordering logic
        inv_pos = on_hand + sum(q for _, q in pipeline)
        order_qty = 0.0
        pt = cfg.policy_type.upper()

        if pt in ("EOQ", "ROP"):
            rop = cfg.reorder_point or 0.0
            if inv_pos <= rop:
                order_qty = cfg.order_qty or max(1.0, cfg.annual_demand / 12.0)

        elif pt == "MINMAX":
            s = cfg.min_inv or 0.0
            S = cfg.max_inv or 0.0
            if inv_pos <= s:
                order_qty = max(0.0, S - inv_pos)

        elif pt == "PERIODIC":
            if not cfg.review_period_days or cfg.review_period_days <= 0:
                cfg.review_period_days = max(1, cfg.lead_time_days)
            if day % cfg.review_period_days == 0:
                target = cfg.max_inv or 0.0
                order_qty = max(0.0, target - inv_pos)

        # Ordenar si hay cantidad
        if order_qty > 0:
            lt = draw_lead_time(cfg, rng)
            pipeline.append((day + lt, order_qty))
            num_orders += 1
            ordering += cfg.order_cost_fixed

        # 4) Inventory & costs
        sum_inv += on_hand
        holding += on_hand * holding_per_day

        daily_states.append(
            DailyState(
                day=day,
                on_hand=on_hand,
                on_order=sum(q for _, q in pipeline),
                demand=demand,
                shipped=shipped,
                stockout=stockout,
            )
        )

    avg_inv = sum_inv / sim_days if sim_days > 0 else 0.0
    avg_inv_value = avg_inv * cfg.unit_cost
    total_cost = holding + ordering + stockout_cost
    fill_rate = 100.0 * filled_dem / total_dem if total_dem > 0 else 0.0

    return SkuResult(
        sku_id=cfg.sku_id,
        name=cfg.name,
        policy_type=cfg.policy_type,
        total_demand=total_dem,
        filled_demand=filled_dem,
        fill_rate_pct=fill_rate,
        avg_inventory=avg_inv,
        avg_inventory_value=avg_inv_value,
        unit_cost=cfg.unit_cost,
        stockout_days=stockout_days,
        num_orders=num_orders,
        total_cost=total_cost,
        holding_cost=holding,
        ordering_cost=ordering,
        stockout_cost=stockout_cost,
        daily_states=daily_states,
    )


def build_insights(
    results: List[SkuResult],
    sim_days: int,
    service: float,
) -> Dict[str, Any]:
    """Simple, explainable inventory insights for the UI."""
    if not results:
        return {"messages": ["No SKUs simulated."], "highlights": {}}

    msgs: List[str] = []
    highlights: Dict[str, Any] = {}

    avg_fill = sum(r.fill_rate_pct for r in results) / len(results)
    total_cost = sum(r.total_cost for r in results)

    msgs.append(
        f"Simulated {len(results)} SKUs over {sim_days} days with target service level {service:.1%}."
    )
    msgs.append(
        f"Portfolio achieved an average fill rate of {avg_fill:.2f}% with total cost {total_cost:,.2f} €."
    )

    best = max(results, key=lambda r: r.fill_rate_pct)
    worst = min(results, key=lambda r: r.fill_rate_pct)
    high_cost = max(results, key=lambda r: r.total_cost)

    highlights["best_fill_sku"] = {
        "sku": best.sku_id,
        "name": best.name,
        "fill_rate": round(best.fill_rate_pct, 2),
        "policy": best.policy_type,
    }
    highlights["worst_fill_sku"] = {
        "sku": worst.sku_id,
        "name": worst.name,
        "fill_rate": round(worst.fill_rate_pct, 2),
        "policy": worst.policy_type,
    }
    highlights["highest_cost_sku"] = {
        "sku": high_cost.sku_id,
        "name": high_cost.name,
        "total_cost": round(high_cost.total_cost, 2),
        "policy": high_cost.policy_type,
    }

    msgs.append("Inventory Copilot Recommendations:")
    for r in results:
        parts: List[str] = []
        if r.fill_rate_pct < 95:
            parts.append(f"Low service level ({r.fill_rate_pct:.1f}%) – consider increasing safety stock.")
        if r.fill_rate_pct > 99.5 and r.avg_inventory > r.total_demand / 30:
            parts.append("Very high service level – may be overstocking.")
        if r.stockout_days > 0:
            parts.append(
                f"{r.stockout_days} stockout days – check reorder parameters."
            )
        if r.num_orders == 0 and r.policy_type not in ["JIT", "PERIODIC"]:
            parts.append("No orders placed – check initial inventory levels.")
        if not parts:
            parts.append("Balanced performance under current assumptions.")
        msgs.append(f"SKU {r.sku_id} ({r.name}): " + " ".join(parts))

    return {"messages": msgs, "highlights": highlights}


def simulate_portfolio(
    skus: List[Dict[str, Any]],
    simulation_days: int = 365,
    service_level: float = 0.95,
    rng_seed: int = 42,
) -> Dict[str, Any]:
    """
    Main entry point used by the Flask backend.

    skus: list of dictionaries coming from the frontend or CSV.
    """
    results: List[SkuResult] = []
    for i, s in enumerate(skus, start=1):
        # Extraer valores con manejo de nulos
        sku_id = str(s.get("skuId", i))
        name = str(s.get("name", f"SKU {i}"))
        
        # Asegurar que los valores numéricos no sean None
        annual_demand = float(s.get("annualDemand", 10000.0) or 10000.0)
        demand_std_pct = float(s.get("demandStdPct", 0.2) or 0.2)
        lead_time_days = int(s.get("leadTimeDays", 7) or 7)
        lead_time_std_pct = float(s.get("leadTimeStdPct", 0.1) or 0.1)
        unit_cost = float(s.get("unitCost", 10.0) or 10.0)
        holding_cost_pct = float(s.get("holdingCostPct", 0.25) or 0.25)
        order_cost_fixed = float(s.get("orderCostFixed", 50.0) or 50.0)
        stockout_cost_per_unit = float(s.get("stockoutCostPerUnit", 20.0) or 20.0)
        policy_type = str(s.get("policyType", "EOQ") or "EOQ").upper()
        
        cfg = SkuConfig(
            sku_id=sku_id,
            name=name,
            annual_demand=annual_demand,
            demand_std_pct=demand_std_pct,
            lead_time_days=lead_time_days,
            lead_time_std_pct=lead_time_std_pct,
            unit_cost=unit_cost,
            holding_cost_pct=holding_cost_pct,
            order_cost_fixed=order_cost_fixed,
            stockout_cost_per_unit=stockout_cost_per_unit,
            policy_type=policy_type,
            reorder_point=s.get("reorderPoint"),
            order_qty=s.get("orderQty"),
            min_inv=s.get("minInv"),
            max_inv=s.get("maxInv"),
            review_period_days=s.get("reviewPeriodDays"),
            seasonality_enabled=bool(s.get("seasonalityEnabled", True)),
            seasonality_amplitude=float(
                s.get("seasonalityAmplitude", 0.2) or 0.2
            ),
            trend_pct_per_year=float(s.get("trendPctPerYear", 0.0) or 0.0),
        )
        res = simulate_single_sku(cfg, simulation_days, service_level, seed=rng_seed + i)
        results.append(res)

    tot_cost = sum(r.total_cost for r in results)
    tot_dem = sum(r.total_demand for r in results)
    avg_fill = (
        sum(r.fill_rate_pct for r in results) / len(results) if results else 0.0
    )
    cpu = tot_cost / tot_dem if tot_dem > 0 else 0.0
    insights = build_insights(results, simulation_days, service_level)

    skus_payload: List[Dict[str, Any]] = []
    for r in results:
        skus_payload.append(
            {
                "SkuId": r.sku_id,
                "Name": r.name,
                "Policy": r.policy_type,
                "Total_Demand": round(r.total_demand, 2),
                "Filled_Demand": round(r.filled_demand, 2),
                "Fill_Rate": round(r.fill_rate_pct, 2),
                "Avg_Inventory": round(r.avg_inventory, 2),
                "Avg_Inventory_Value": round(r.avg_inventory_value, 2),
                "Unit_Cost": round(r.unit_cost, 2),
                "Stockout_Days": r.stockout_days,
                "Num_Orders": r.num_orders,
                "Total_Cost": round(r.total_cost, 2),
                "Holding_Cost": round(r.holding_cost, 2),
                "Ordering_Cost": round(r.ordering_cost, 2),
                "Stockout_Cost": round(r.stockout_cost, 2),
                "Daily_States": [
                    {
                        "Day": ds.day,
                        "On_Hand": round(ds.on_hand, 2),
                        "On_Order": round(ds.on_order, 2),
                        "Demand": round(ds.demand, 2),
                        "Shipped": round(ds.shipped, 2),
                        "Stockout": ds.stockout,
                    }
                    for ds in r.daily_states
                ],
            }
        )

    return {
        "Simulation_Days": simulation_days,
        "Average_Fill_Rate": round(avg_fill, 2),
        "SKUs": skus_payload,
        "Total_Cost": round(tot_cost, 2),
        "Cost_per_Unit_Demand": round(cpu, 4),
        "Insights": insights,
    }
