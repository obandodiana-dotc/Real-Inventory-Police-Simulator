<div align="center">

# 📦 Real Inventory Policy Simulator  
### Turning inventory theory into real operational decisions

**A data-driven simulator to explore how inventory policies impact service level, cost, and stockout risk — in realistic supply chain scenarios.**

Built as a **Final Project** for  
🎓 *ReDI School of Digital Integration — Introduction to Coding, Data, and Design*

---

[🚀 Live Demo](#) · [📄 Documentation](#how-it-works) · [📊 CSV Template](#csv-import) · [🧭 Roadmap](#roadmap)

</div>

---

## 🧠 Why this project exists

Inventory decisions are rarely black or white.

Increasing service levels often means higher costs.  
Reducing inventory may improve cash flow but increase stockout risk.  
And **fast movers behave very differently from slow movers**.

This simulator was built to **make those trade-offs visible**.

Instead of static formulas, it allows users to **experiment, simulate, and learn** how inventory policies behave under variability and uncertainty — using realistic operational inputs.

---

## ⚙️ What the simulator does

✔ Simulates inventory behavior over time  
✔ Compares multiple replenishment policies per SKU  
✔ Visualizes **cost vs service trade-offs**  
✔ Highlights differences between **fast-moving and slow-moving products**  
✔ Supports scenario-based analysis with variability  

---

## 🔍 Key insights you can explore

- How demand variability affects safety stock and fill rate  
- Why one policy works for fast movers but fails for slow movers  
- The real cost of stockouts vs holding excess inventory  
- How lead time variability amplifies operational risk  

---

## 🧩 Core features

- **Scenario setup**
  - Simulation horizon
  - Target service level
  - Demand & lead time variability sliders

- **SKU-level configuration**
  - Annual demand
  - Lead time
  - Unit, holding, ordering, and stockout costs
  - Policy selection per SKU

- **Policy comparison**
  - EOQ
  - Reorder Point (ROP)
  - Min-Max
  - Periodic Review

- **Results & KPIs**
  - Fill rate / service level
  - Total inventory cost
  - Stockout risk indicators

- **CSV Import / Export**
  - Run simulations with real or synthetic SKU data

---

## 🧪 How it works

1️⃣ **Define the scenario**  
Set the environment: variability, horizon, and service targets.

2️⃣ **Configure SKUs**  
Each SKU can follow a different inventory policy.

3️⃣ **Run the simulation**  
The system simulates inventory behavior day by day.

4️⃣ **Analyze results**  
Compare KPIs, identify trade-offs, and extract insights.

---

## 📊 Example CSV format

```csv
sku,name,annual_demand,lead_time_days,unit_cost,holding_cost_rate,order_cost,stockout_cost,policy
SKU1,Sneaker - Fast mover,24000,7,45,0.25,80,60,EOQ
SKU2,Boot - Slow mover,6000,21,90,0.30,100,120,ROP
