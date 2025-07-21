# 🔬 PathLinker: Gene → Protein → Pathway Explorer

**PathLinker** is an interactive web dashboard built for wet lab scientists and computational biologists to visualize the molecular relationships between input genes, their associated proteins, and biological pathways.

This tool helps researchers:
- Explore known protein-protein interactions.
- Map genes to human pathways using KEGG.
- Detect shared pathways or interactors among multiple genes.
- Generate interactive networks in seconds.

---

## 🧪 Use Case

**PathLinker** is ideal for:
- Hypothesis generation in functional genomics.
- Interpreting transcriptomic or CRISPR screen hits.
- Exploring molecular crosstalk and shared biological mechanisms.
- Quickly validating gene function associations based on curated pathway data.

> **Example:**  
> Inputting genes like `TP53, BRCA1, EGFR, MYC` allows you to identify overlap in cancer-related pathways and explore how these genes connect through proteins in STRING DB.

---

## 🚀 Features

- 🧬 Map genes to STRING protein interactions.
- 🧠 Retrieve pathway associations from KEGG (hsa).
- 🎯 Filter by pathway keyword (e.g. "cancer", "cell cycle").
- 🧭 Dynamic graph layout with color-coded node types:
  - Blue: Input genes
  - Red: Pathways
  - Green: Interacting proteins
- 🖱️ Interactive: Zoom, drag, highlight, and explore.

---

## ⚙️ How to Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/pathlinker.git
cd pathlinker

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt

python app.py

```

Then open http://127.0.0.1:8050 in your browser.

## 2. 📝 Example Input
```text
TP53, BRCA1, EGFR, MYC

Optional Keyword Filter:
cancer

```

## 📂 Project Structure

```bash
├── app.py                # Main Dash app
├── README.md             # Project documentation
├── requirements.txt      # Dependencies
```

## 📡 Data Sources

🔗 STRING DB for protein-protein interaction networks.

🔗 KEGG for pathway mapping (human-specific).

## 📢 Notes

- Only Homo sapiens (human) genes are supported (hsa: prefix in KEGG).

- You can input up to 10 genes at a time to respect API usage limits.

- For best results, use official gene symbols (e.g., TP53, not aliases like p53).

## 🤝 Acknowledgments

Special thanks to:

- The KEGG and STRING DB teams for maintaining high-quality biological databases.

- The Dash and Cytoscape communities for enabling interactive bioinformatics visualization.