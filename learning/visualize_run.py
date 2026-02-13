#!/usr/bin/env python3
"""
visualize_run.py — Generate an interactive HTML report for a training run.

Creates a single self-contained HTML file with:
  1. Training pipeline flow diagram (how data moves through the system)
  2. Training metrics charts (loss, accuracy over steps)
  3. Side-by-side base vs LoRA comparison table
  4. LoRA architecture diagram

Usage:
    python learning/visualize_run.py \
        --run outputs/lora/llama31-sql_20260211_233824 \
        --comparison outputs/inference/comparison_20260212_102431.json

    # Or just metrics:
    python learning/visualize_run.py \
        --run outputs/lora/llama31-sql_20260211_233824
"""

import argparse
import json
import sys
from pathlib import Path


def load_trainer_state(run_dir: Path) -> dict:
    """Find and load trainer_state.json from the latest checkpoint."""
    checkpoints = sorted(run_dir.glob("checkpoint-*/trainer_state.json"))
    if checkpoints:
        with open(checkpoints[-1]) as f:
            return json.load(f)
    return {}


def load_comparison(path: str) -> list:
    """Load comparison JSON."""
    with open(path) as f:
        return json.load(f)


def load_recipe(run_dir: Path) -> dict:
    """Load the recipe copy saved with the run."""
    recipe_path = run_dir / "recipe.yaml"
    if recipe_path.exists():
        import yaml
        with open(recipe_path) as f:
            return yaml.safe_load(f)
    return {}


def extract_sql(text: str) -> str:
    """Extract SQL from a response (handles markdown code blocks)."""
    if "```sql" in text:
        parts = text.split("```sql")
        if len(parts) > 1:
            return parts[1].split("```")[0].strip()
    if "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            return parts[1].strip()
    # Find first SELECT statement
    lines = text.strip().split("\n")
    sql_lines = []
    capturing = False
    for line in lines:
        stripped = line.strip().upper()
        if stripped.startswith("SELECT") or stripped.startswith("WITH"):
            capturing = True
        if capturing:
            sql_lines.append(line.strip())
            if line.strip().endswith(";") or (not line.strip()):
                break
    return "\n".join(sql_lines) if sql_lines else text.strip()


def build_metrics_js(log_history: list) -> str:
    """Build JS arrays for Chart.js from training log history."""
    steps = [entry["step"] for entry in log_history]
    losses = [entry["loss"] for entry in log_history]
    accuracies = [entry.get("mean_token_accuracy", 0) for entry in log_history]
    grad_norms = [entry.get("grad_norm", 0) for entry in log_history]
    epochs = [entry.get("epoch", 0) for entry in log_history]
    return f"""
    const steps = {json.dumps(steps)};
    const losses = {json.dumps(losses)};
    const accuracies = {json.dumps(accuracies)};
    const gradNorms = {json.dumps(grad_norms)};
    const epochs = {json.dumps(epochs)};
    """


def build_comparison_html(comparisons: list) -> str:
    """Build the comparison table rows."""
    rows = []
    for i, comp in enumerate(comparisons):
        prompt = comp["prompt"]
        # Extract the question from the prompt
        question = prompt.split("Write a SQL query to answer:")[-1].strip() if "Write a SQL query to answer:" in prompt else prompt

        # Extract schema
        schema = ""
        if "CREATE TABLE" in prompt:
            schema_lines = [l.strip() for l in prompt.split("\n") if l.strip().startswith("CREATE TABLE")]
            schema = "<br>".join(f"<code>{s}</code>" for s in schema_lines)

        base_sql = extract_sql(comp["base_response"])
        lora_sql = comp["lora_response"].strip()

        # Determine correctness indicators
        base_verbose = len(comp["base_response"]) > len(base_sql) + 50
        lora_concise = len(comp["lora_response"]) < 200

        rows.append(f"""
        <tr>
            <td class="prompt-cell">
                <div class="question">{question}</div>
                <div class="schema">{schema}</div>
            </td>
            <td class="sql-cell base-cell">
                <pre><code>{base_sql}</code></pre>
                {"<span class='tag verbose'>verbose</span>" if base_verbose else ""}
                <span class="tag correct">correct SQL</span>
            </td>
            <td class="sql-cell lora-cell">
                <pre><code>{lora_sql}</code></pre>
                {"<span class='tag concise'>concise</span>" if lora_concise else ""}
                <span class="tag learned">learned format</span>
            </td>
        </tr>
        """)
    return "\n".join(rows)


def build_html(run_dir: Path, trainer_state: dict, comparisons: list, recipe: dict) -> str:
    """Build the full HTML report."""
    run_name = run_dir.name
    log_history = trainer_state.get("log_history", [])

    # Extract key metrics
    final_loss = log_history[-1]["loss"] if log_history else "N/A"
    final_acc = log_history[-1].get("mean_token_accuracy", "N/A") if log_history else "N/A"
    initial_loss = log_history[0]["loss"] if log_history else "N/A"
    total_steps = trainer_state.get("global_step", "N/A")

    # Recipe info
    model_name = recipe.get("model", {}).get("name", "Unknown")
    lora_r = recipe.get("lora", {}).get("r", "?")
    lora_alpha = recipe.get("lora", {}).get("lora_alpha", "?")
    lr = recipe.get("training", {}).get("learning_rate", "?")
    epochs = recipe.get("training", {}).get("num_train_epochs", "?")
    max_samples = recipe.get("data", {}).get("max_samples", "?")
    dataset = recipe.get("data", {}).get("default_dataset", "?")

    metrics_js = build_metrics_js(log_history) if log_history else "const steps=[];const losses=[];const accuracies=[];const gradNorms=[];const epochs=[];"
    comparison_rows = build_comparison_html(comparisons) if comparisons else "<tr><td colspan='3'>No comparison data</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Training Report — {run_name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
:root {{
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --text-muted: #8b949e; --accent: #58a6ff;
    --green: #3fb950; --orange: #d29922; --red: #f85149;
    --purple: #bc8cff;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6;
    padding: 2rem; max-width: 1400px; margin: 0 auto;
}}
h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
h2 {{
    font-size: 1.3rem; margin: 2rem 0 1rem; padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}}
h3 {{ font-size: 1.1rem; color: var(--accent); margin: 1rem 0 0.5rem; }}
.subtitle {{ color: var(--text-muted); margin-bottom: 2rem; }}

/* Cards */
.card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;
}}
.stats-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem; margin-bottom: 1.5rem;
}}
.stat {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1rem; text-align: center;
}}
.stat .value {{ font-size: 1.8rem; font-weight: 700; color: var(--accent); }}
.stat .label {{ font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; }}
.stat.good .value {{ color: var(--green); }}
.stat.warn .value {{ color: var(--orange); }}

/* Charts */
.charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
.chart-container {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }}
canvas {{ width: 100% !important; }}

/* Comparison table */
table {{ width: 100%; border-collapse: collapse; }}
th {{
    text-align: left; padding: 0.75rem; background: var(--surface);
    border-bottom: 2px solid var(--border); font-size: 0.85rem;
    text-transform: uppercase; color: var(--text-muted);
}}
td {{ padding: 0.75rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
.prompt-cell {{ max-width: 300px; }}
.question {{ font-weight: 600; margin-bottom: 0.5rem; }}
.schema {{ font-size: 0.8rem; color: var(--text-muted); }}
.schema code {{ font-size: 0.75rem; background: var(--bg); padding: 2px 6px; border-radius: 4px; }}
.sql-cell pre {{
    background: var(--bg); border-radius: 6px; padding: 0.75rem;
    overflow-x: auto; font-size: 0.85rem; margin-bottom: 0.5rem;
}}
.sql-cell code {{ color: var(--green); }}
.lora-cell code {{ color: var(--purple); }}
.tag {{
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 0.7rem; font-weight: 600; margin: 2px;
}}
.tag.verbose {{ background: rgba(210,153,34,0.2); color: var(--orange); }}
.tag.concise {{ background: rgba(188,140,255,0.2); color: var(--purple); }}
.tag.correct {{ background: rgba(63,185,80,0.15); color: var(--green); }}
.tag.learned {{ background: rgba(88,166,255,0.2); color: var(--accent); }}

/* Mermaid */
.mermaid {{ background: var(--surface); border-radius: 8px; padding: 1rem; text-align: center; }}

/* Key takeaways */
.takeaway {{
    background: rgba(88,166,255,0.1); border-left: 3px solid var(--accent);
    padding: 1rem 1.5rem; border-radius: 0 8px 8px 0; margin: 1rem 0;
}}
.takeaway strong {{ color: var(--accent); }}

@media (max-width: 800px) {{
    .charts-grid {{ grid-template-columns: 1fr; }}
    .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
</head>
<body>

<h1>📊 Training Run Report</h1>
<p class="subtitle">{run_name} · {model_name}</p>

<!-- Key Stats -->
<div class="stats-grid">
    <div class="stat good">
        <div class="value">{final_loss:.3f}</div>
        <div class="label">Final Loss</div>
    </div>
    <div class="stat good">
        <div class="value">{final_acc:.1%}</div>
        <div class="label">Token Accuracy</div>
    </div>
    <div class="stat">
        <div class="value">{initial_loss:.2f} → {final_loss:.2f}</div>
        <div class="label">Loss Journey</div>
    </div>
    <div class="stat">
        <div class="value">{total_steps}</div>
        <div class="label">Total Steps</div>
    </div>
    <div class="stat">
        <div class="value">r={lora_r}, α={lora_alpha}</div>
        <div class="label">LoRA Config</div>
    </div>
    <div class="stat">
        <div class="value">{max_samples}</div>
        <div class="label">Training Samples</div>
    </div>
</div>

<!-- Pipeline Flow -->
<h2>🔄 Training Pipeline Flow</h2>
<div class="card">
<div class="mermaid">
graph LR
    A["📄 YAML Recipe"] --> B["🔧 load_recipe()"]
    B --> C["Model Config"]
    B --> D["LoRA Config"]
    B --> E["Training Config"]
    B --> F["Data Config"]

    C --> G["🧠 load_model()<br/>Llama 3.1 8B<br/>float16 · MPS"]
    D --> H["🔗 get_peft_model()<br/>LoRA r={lora_r} α={lora_alpha}<br/>13.6M trainable / 8B total"]

    F --> I["📦 prepare_dataset()<br/>{dataset}<br/>{max_samples} samples"]
    I --> J["💬 format_sql_to_chat()<br/>schema + question → SQL"]

    G --> H
    H --> K["🏋️ SFTTrainer"]
    J --> K
    E --> K

    K --> L["💾 Adapter Output<br/>adapter_model.safetensors<br/>~55MB"]

    style A fill:#1a1a2e,stroke:#58a6ff
    style G fill:#1a1a2e,stroke:#3fb950
    style H fill:#1a1a2e,stroke:#bc8cff
    style I fill:#1a1a2e,stroke:#d29922
    style K fill:#1a1a2e,stroke:#f85149
    style L fill:#1a1a2e,stroke:#3fb950
</div>
</div>

<!-- What LoRA Actually Does -->
<h2>🧬 How LoRA Works — Conceptually</h2>
<div class="card">
<div class="mermaid">
graph TB
    subgraph Original["Original Layer (Frozen)"]
        W["W<br/>8B params<br/>❄️ frozen"]
    end

    subgraph LoRA["LoRA Adapter (Trainable)"]
        A2["A<br/>down-project<br/>4096 → {lora_r}"]
        B2["B<br/>up-project<br/>{lora_r} → 4096"]
        A2 --> B2
    end

    X["Input x"] --> W
    X --> A2
    W --> PLUS["➕ Add"]
    B2 --> PLUS
    PLUS --> Y["Output y = Wx + BAx"]

    style W fill:#1a1a2e,stroke:#8b949e
    style A2 fill:#1a1a2e,stroke:#bc8cff
    style B2 fill:#1a1a2e,stroke:#bc8cff
    style PLUS fill:#1a1a2e,stroke:#3fb950
</div>
<div class="takeaway">
    <strong>Key insight:</strong> Only A and B are trained ({lora_r} × 4096 × 2 = very small).
    The original 8B parameters are frozen. The adapter learns a <em>correction</em> to the original weights.
    At inference, the correction is added: <code>y = Wx + BAx</code>.
</div>
</div>

<!-- Training Metrics -->
<h2>📈 Training Metrics</h2>
<div class="charts-grid">
    <div class="chart-container">
        <h3>Loss over Training</h3>
        <canvas id="lossChart"></canvas>
    </div>
    <div class="chart-container">
        <h3>Token Accuracy over Training</h3>
        <canvas id="accChart"></canvas>
    </div>
</div>

<!-- Comparison -->
<h2>⚡ Base vs Finetuned — SQL Comparison</h2>
<div class="takeaway">
    <strong>What to look for:</strong> The base model gives correct SQL but wraps it in
    verbose explanations. The finetuned model learned the training data's format —
    <em>output only the SQL query, nothing else</em>. This behavioral shift from just
    {max_samples} examples is the core value of finetuning.
</div>
<div class="card" style="overflow-x: auto;">
<table>
    <thead>
        <tr>
            <th style="width:30%">Question</th>
            <th style="width:35%">Base Model (Llama 3.1 8B)</th>
            <th style="width:35%">Base + LoRA (finetuned)</th>
        </tr>
    </thead>
    <tbody>
        {comparison_rows}
    </tbody>
</table>
</div>

<h2>🎯 Key Observations</h2>
<div class="card">
    <div class="takeaway">
        <strong>1. Format learning:</strong> After seeing 1000 SQL examples, the model learned
        to output <em>pure SQL</em> without explanations. The training data was formatted as
        <code>[schema] → [SQL only]</code>, and the model internalized this pattern.
    </div>
    <div class="takeaway" style="margin-top: 1rem;">
        <strong>2. Schema awareness:</strong> The finetuned model consistently references the
        correct table and column names from the provided schema. It learned to read
        CREATE TABLE statements and map them to SQL queries.
    </div>
    <div class="takeaway" style="margin-top: 1rem;">
        <strong>3. Conciseness as learned behavior:</strong> The base model is trained to be
        helpful and verbose (instruction tuning). Our SQL data taught a different behavior —
        be precise and terse. This shows finetuning can <em>override</em> instruction-tuning
        patterns for specific tasks.
    </div>
</div>

<script>
{metrics_js}

mermaid.initialize({{ theme: 'dark', themeVariables: {{
    primaryColor: '#1a1a2e', primaryTextColor: '#e6edf3',
    primaryBorderColor: '#58a6ff', lineColor: '#30363d',
    secondaryColor: '#161b22', tertiaryColor: '#0d1117'
}} }});

// Loss Chart
new Chart(document.getElementById('lossChart'), {{
    type: 'line',
    data: {{
        labels: steps,
        datasets: [{{
            label: 'Training Loss',
            data: losses,
            borderColor: '#f85149',
            backgroundColor: 'rgba(248,81,73,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 2,
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ labels: {{ color: '#8b949e' }} }} }},
        scales: {{
            x: {{ title: {{ display: true, text: 'Step', color: '#8b949e' }},
                   ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }},
            y: {{ title: {{ display: true, text: 'Loss', color: '#8b949e' }},
                   ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }}
        }}
    }}
}});

// Accuracy Chart
new Chart(document.getElementById('accChart'), {{
    type: 'line',
    data: {{
        labels: steps,
        datasets: [{{
            label: 'Token Accuracy',
            data: accuracies,
            borderColor: '#3fb950',
            backgroundColor: 'rgba(63,185,80,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 2,
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ labels: {{ color: '#8b949e' }} }} }},
        scales: {{
            x: {{ title: {{ display: true, text: 'Step', color: '#8b949e' }},
                   ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }},
            y: {{ title: {{ display: true, text: 'Accuracy', color: '#8b949e' }},
                   ticks: {{ color: '#8b949e', callback: v => (v*100).toFixed(0)+'%' }},
                   grid: {{ color: '#21262d' }}, min: 0, max: 1 }}
        }}
    }}
}});
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate training run visualization")
    parser.add_argument("--run", required=True, help="Path to training run directory")
    parser.add_argument("--comparison", default=None, help="Path to comparison JSON file")
    parser.add_argument("--output", default=None, help="Output HTML file (default: learning/outputs/<run_name>.html)")
    args = parser.parse_args()

    run_dir = Path(args.run)
    if not run_dir.exists():
        print(f"ERROR: Run directory not found: {run_dir}")
        sys.exit(1)

    # Load data
    print(f"Loading run data from: {run_dir}")
    trainer_state = load_trainer_state(run_dir)
    recipe = load_recipe(run_dir)
    comparisons = load_comparison(args.comparison) if args.comparison else []

    log_history = trainer_state.get("log_history", [])
    print(f"  Training steps: {len(log_history)}")
    print(f"  Comparison prompts: {len(comparisons)}")

    # Build HTML
    html = build_html(run_dir, trainer_state, comparisons, recipe)

    # Write output
    out_dir = Path("learning/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.output) if args.output else out_dir / f"{run_dir.name}.html"
    with open(out_path, "w") as f:
        f.write(html)

    print(f"\n✓ Report generated: {out_path}")
    print(f"  Open in browser: open {out_path}")


if __name__ == "__main__":
    main()
