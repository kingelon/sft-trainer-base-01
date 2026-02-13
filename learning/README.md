# Learning — Visualizations & Understanding

Scripts that generate visual reports to build intuition about the training and inference pipeline.

## Structure
```
learning/
├── README.md
├── visualize_run.py       # Generate HTML report for a training run
└── outputs/               # Generated reports go here
    └── *.html
```

## Usage

```bash
# Full report (metrics + comparison)
python learning/visualize_run.py \
    --run outputs/lora/llama31-sql_20260211_233824 \
    --comparison outputs/inference/comparison_20260212_102431.json

# Metrics only
python learning/visualize_run.py \
    --run outputs/lora/llama31-sql_20260211_233824
```

Open the generated HTML file in your browser to view the interactive report.

## What the Report Shows

1. **Key Stats** — Final loss, token accuracy, LoRA config, samples
2. **Pipeline Flow** — Mermaid diagram showing how data flows through training
3. **LoRA Architecture** — How the low-rank decomposition works conceptually
4. **Training Curves** — Interactive Chart.js charts for loss and accuracy
5. **Comparison Table** — Base vs finetuned SQL output side-by-side
6. **Key Observations** — What the results tell us about finetuning
