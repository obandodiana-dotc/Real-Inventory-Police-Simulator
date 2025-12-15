# Real-Inventory-Police-Simulator

A web-based simulator to **compare inventory policies** and visualize how decisions impact **service level (fill rate), total cost, and stockout risk**—across **fast movers** and **slow movers**.

Built as a final project for **ReDI School of Digital Integration** (Introduction to Coding, Data, and Design).

---

## What this project does

This simulator helps you answer questions like:

- What happens to **fill rate** and **total cost** if demand/lead time variability increases?
- Which policy performs better for **fast-moving vs slow-moving SKUs**?
- What trade-offs exist between **service level** and **cost**?

It supports scenario-based analysis and per-SKU policy configuration.

---

## Key features

- **Scenario setup** (simulation horizon, target service level, variability sliders)
- **Multi-SKU configuration** (demand, lead time, costs, policy per SKU)
- Policy comparison (e.g., **EOQ, ROP, Min-Max, Periodic Review**)
- KPI outputs (cost, service level/fill rate, stockout risk)
- **CSV export/import** to run simulations with real SKU datasets
- Clean UI with an **Analyst / Management** view (optional)

---

## Screenshots

> Add images to `/assets/` and update the paths below.

![Simulator UI](assets/simulator-ui.png)
![Results](assets/results.png)

---

## Inventory policies supported (example)

- **EOQ** (Economic Order Quantity)
- **ROP** (Reorder Point)
- **Min-Max**
- **Periodic Review**

> Note: Exact implementation depends on your model assumptions (lost sales vs backorders, review frequency, etc.).

---

## Tech stack

- Frontend: `HTML / CSS / JavaScript` (or your framework if applicable)
- Backend/API (optional): `Python` (or Node) for simulation logic
- Version control: `Git & GitHub`

> Update this section to match your real stack.

---

## Getting started

### 1) Clone the repo

```bash
git clone https://github.com/<your-username>/real-inventory-policy-simulator.git
cd real-inventory-policy-simulator
