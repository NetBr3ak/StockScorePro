# 📈 **StockScorePro: Your Smart Investment Assistant**

StockScorePro is an intelligent and user-friendly investment tool designed to analyze stocks based on their current prices relative to their 50-day moving average. It identifies attractive investment opportunities by evaluating price stability, closeness to average pricing, and potential undervaluation. 💰📊

---

## 🚀 **How Does StockScorePro Work?**

StockScorePro evaluates each stock using three clear indicators:

- **Stability 🧘**:  
  *How stable has the stock’s average price been recently?*  
  **Example:** If a stock’s average price has barely changed in recent days, it scores close to 1 (very stable).

- **Closeness 🎯**:  
  *How close is the current stock price to its 50-day average?*  
  **Example:** If a stock’s current price matches its 50-day average, the Closeness score is 1 (perfect match).

- **ExtraValue ✨**:  
  *Is the stock priced below its 50-day average, potentially offering extra value?*  
  **Example:** A stock trading 5% below its average receives a 5% bonus (ExtraValue score: 1.05).

These indicators combine into a single **OverallScore 🏅**, making it easy for you to spot attractive investment opportunities quickly.

---

## 🛠️ **Installation & Quick Start**

Follow these simple steps to start using StockScorePro:

### **1. Install Required Libraries**

```bash  
pip install yfinance pandas numpy  
```

### **2. Run StockScorePro**

Save the provided Python script as `stockscorepro.py`.

- Run with the default monthly investment amount ($3000):

```bash  
python stockscorepro.py  
```

- Run specifying your own investment amount (e.g., $1500):

```bash  
python stockscorepro.py --capital 1500  
```

---

## 🔍 **Example Results**

When you run StockScorePro, you'll get clear results like this:

```bash  
Evaluation results (higher OverallScore indicates a potentially better investment):

    Company  LatestPrice  50DayAverage  PriceDifferencePercent  Stability  Closeness  ExtraValue  OverallScore
      Apple        145.3          150.0                  -0.031      0.980      0.920       1.031          0.930
  Microsoft        290.5          289.0                   0.005      0.995      0.990       1.000          0.985
       Nike        120.2          125.0                  -0.038      0.970      0.880       1.038          0.886

Proposed investment distribution based on your monthly budget:

    Company  InvestmentFraction  InvestmentAmount
      Apple              0.332             996.00
  Microsoft              0.352            1056.00
       Nike              0.316             948.00

Analysis completed on: 2025-03-13 15:45:30  
```
---

## 📌 **Why Use StockScorePro?**

- ✅ **Clear & Practical**: Easily identify attractive stocks without complicated analysis.
- ✅ **Data-Driven**: Make decisions using reliable market information.
- ✅ **Time Efficient**: Quickly evaluate multiple stocks simultaneously.
- ✅ **Optimized Investment**: Automatically distribute your capital efficiently.

---

## ⚠️ **Important Disclaimer**

StockScorePro is intended for educational purposes. Always do additional research before investing. Investing involves risk, and past performance does not guarantee future returns.

---

## 📩 **Contact & Contribution**

Got feedback or questions? Feel free to reach out and help improve StockScorePro!

💡 **Happy Investing!** 🚀🌟
