# 🛡 Solana TX Risk Checker

This tool evaluates the **risk level of Solana transactions** using domain-based address matching and behavioral analysis.

✅ Built for identifying **dusting attacks**  
✅ Uses real-time on-chain data from Flipside Crypto  
✅ Outputs a risk score and label (`High Risk`, `Medium Risk`, etc.) for each transaction  

---

## 🧠 Methodology

The tool compares transaction participants based on:
- Partial string matches of `tx_from` and `tx_to` addresses
- Transfer size thresholds (small amounts for potential dusting)
- Wallet funding recency
- Price-weighted volume thresholds

It assigns a score between 0–100 and a label indicating the severity of the transaction's risk profile.

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## 🚀 Setup

```bash
git clone https://github.com/YOUR_USERNAME/solana-tx-risk-checker.git
cd solana-tx-risk-checker
pip install -r requirements.txt
