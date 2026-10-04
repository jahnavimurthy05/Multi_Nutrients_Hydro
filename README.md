# HydroEco Grow (Multi-Crop Hydroponics Optimizer & Monitor)

🌱 An IoT-enabled hydroponic monitoring system with genetic-algorithm-powered multi-crop nutrient optimization.

## 🚀 Live Demo
Visit the live dashboard on GitHub Pages:
[https://jahnavimurthy05.github.io/Multi_Nutrients_Hydro/](https://jahnavimurthy05.github.io/Multi_Nutrients_Hydro/)

---

## 📌 Features
- **Real-Time Sensor Telemetry**: Monitors pH, Temperature, and Humidity via Arduino serial communication (`COM5`).
- **Genetic Algorithm Optimization**: Uses Python's `DEAP` library to find the optimal compromise nutrient solution (pH, EC, N, P, K) for mixed-crop farming.
- **Hydroponic Knowledge Base**:
  - Growing methods: Kratky, Deep Water Culture (DWC), Nutrient Film Technique (NFT), and Wick systems.
  - Crop encyclopedias and companion planting recipes.
  - Critical troubleshooting guidelines for commercial and hobbyist growers.

---

## 🛠️ Local Setup & Running

### 1. Prerequisites
- **Node.js** (v18+)
- **Python 3** with dependencies:
  ```bash
  pip install deap matplotlib numpy
  ```
- **Arduino** (optional for hardware telemetry): Flash DHT and pH sensor sketches reading to serial at 9600 baud.

### 2. Installation
```bash
git clone https://github.com/jahnavimurthy05/Multi_Nutrients_Hydro.git
cd Multi_Nutrients_Hydro
npm install
```

### 3. Start the Server
```bash
node server.js
```
Open [http://localhost:3000](http://localhost:3000) in your browser.
