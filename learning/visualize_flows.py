#!/usr/bin/env python3
"""
visualize_flows.py — Detailed training & inference flow diagrams.

Generates an interactive HTML showing:
  1. Training: function-by-function flow with library boundaries
  2. Inference: how prompts flow through base vs base+LoRA
  3. The real delta: what finetuning actually taught vs prompt engineering

Usage:
    python learning/visualize_flows.py
    open learning/outputs/flow_diagrams.html
"""

from pathlib import Path


def build_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Training & Inference Flows — Deep Dive</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
:root {
    --bg: #0d1117; --surface: #161b22; --surface2: #1c2333;
    --border: #30363d; --text: #e6edf3; --text-muted: #8b949e;
    --accent: #58a6ff; --green: #3fb950; --orange: #d29922;
    --red: #f85149; --purple: #bc8cff; --cyan: #39d353;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.7;
    padding: 2rem 3rem; max-width: 1600px; margin: 0 auto;
}
h1 { font-size: 2rem; margin-bottom: 0.3rem; }
h2 {
    font-size: 1.4rem; margin: 2.5rem 0 1rem; padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}
h3 { font-size: 1.1rem; color: var(--accent); margin: 1.5rem 0 0.5rem; }
.subtitle { color: var(--text-muted); margin-bottom: 2rem; font-size: 0.95rem; }

.card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem;
}
.mermaid {
    background: var(--surface); border-radius: 10px;
    padding: 1.5rem; text-align: center; overflow-x: auto;
}
.callout {
    padding: 1rem 1.5rem; border-radius: 0 8px 8px 0; margin: 1rem 0;
    font-size: 0.95rem;
}
.callout.blue   { background: rgba(88,166,255,0.1); border-left: 3px solid var(--accent); }
.callout.green  { background: rgba(63,185,80,0.1);  border-left: 3px solid var(--green); }
.callout.orange { background: rgba(210,153,34,0.1); border-left: 3px solid var(--orange); }
.callout.red    { background: rgba(248,81,73,0.1);  border-left: 3px solid var(--red); }
.callout.purple { background: rgba(188,140,255,0.1); border-left: 3px solid var(--purple); }
.callout strong { display: inline; }
.callout strong.blue   { color: var(--accent); }
.callout strong.green  { color: var(--green); }
.callout strong.orange { color: var(--orange); }
.callout strong.red    { color: var(--red); }
.callout strong.purple { color: var(--purple); }

/* Code blocks */
pre {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; padding: 1rem; overflow-x: auto;
    font-size: 0.85rem; line-height: 1.5; margin: 0.75rem 0;
}
code { font-family: 'SF Mono', 'Fira Code', monospace; }
.code-inline {
    background: var(--bg); padding: 2px 6px; border-radius: 4px;
    font-size: 0.85rem;
}

/* Two-column layout */
.two-col {
    display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;
    align-items: start;
}
.col-label {
    font-size: 0.85rem; text-transform: uppercase; font-weight: 700;
    color: var(--text-muted); margin-bottom: 0.75rem; letter-spacing: 0.05em;
}

/* Delta section */
.delta-grid {
    display: grid; grid-template-columns: 1fr auto 1fr; gap: 0;
    align-items: stretch;
}
.delta-col {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.25rem;
}
.delta-col.base { border-color: var(--green); }
.delta-col.lora { border-color: var(--purple); }
.delta-sep {
    display: flex; align-items: center; justify-content: center;
    padding: 0 1.5rem; font-size: 1.5rem; color: var(--text-muted);
}
.tag {
    display: inline-block; padding: 2px 10px; border-radius: 12px;
    font-size: 0.75rem; font-weight: 600;
}
.tag.lib     { background: rgba(88,166,255,0.2);  color: var(--accent); }
.tag.our     { background: rgba(63,185,80,0.2);   color: var(--green); }
.tag.frozen  { background: rgba(139,148,158,0.2); color: var(--text-muted); }
.tag.trained { background: rgba(188,140,255,0.2); color: var(--purple); }
.tag.data    { background: rgba(210,153,34,0.2);  color: var(--orange); }

/* Section nav */
.nav {
    position: sticky; top: 0; background: var(--bg); padding: 0.75rem 0;
    border-bottom: 1px solid var(--border); z-index: 10; margin-bottom: 2rem;
}
.nav a {
    color: var(--accent); text-decoration: none; margin-right: 1.5rem;
    font-size: 0.9rem;
}
.nav a:hover { text-decoration: underline; }

@media (max-width: 900px) {
    .two-col, .delta-grid { grid-template-columns: 1fr; }
    .delta-sep { padding: 1rem 0; }
}
</style>
</head>
<body>

<h1>🔬 Training & Inference — Deep Dive</h1>
<p class="subtitle">
    Function-level flows showing exactly what each component does, what libraries handle what,
    and what the real delta is between prompting and finetuning.
</p>

<div class="nav">
    <a href="#training-flow">① Training Flow</a>
    <a href="#training-detail">② Function Detail</a>
    <a href="#inference-flow">③ Inference Flow</a>
    <a href="#real-delta">④ The Real Delta</a>
</div>

<!-- ========================================== -->
<!-- SECTION 1: TRAINING FLOW                   -->
<!-- ========================================== -->
<h2 id="training-flow">① Training Flow — What Happens When You Run <code>train.py</code></h2>

<div class="callout blue">
    <strong class="blue">The big picture:</strong> <code>train.py</code> is an orchestrator.
    It reads a YAML recipe, calls functions from our <code>src/</code> library and three external
    libraries (<code>transformers</code>, <code>peft</code>, <code>trl</code>), then saves the result.
    The actual training loop is handled entirely by <code>trl.SFTTrainer</code>.
</div>

<div class="card">
<div class="mermaid">
graph TB
    subgraph US["<b>📂 Our Code</b>"]
        direction TB
        RECIPE["<b>load_recipe()</b><br/><i>src/config.py</i><br/>YAML → Python dataclasses"]
        TOKENIZER["<b>load_tokenizer()</b><br/><i>src/utils.py</i><br/>Downloads tokenizer from HF"]
        MODEL_LOAD["<b>load_model()</b><br/><i>src/utils.py</i><br/>Downloads 8B model from HF<br/>→ loads in float16 onto MPS"]
        DATA_PREP["<b>prepare_dataset()</b><br/><i>src/utils.py</i><br/>Downloads from HF Hub<br/>→ truncates to max_samples"]
        SQL_FMT["<b>_format_sql_to_chat()</b><br/><i>src/utils.py</i><br/>Converts each example:<br/>schema+question → SQL answer"]
        OUT_DIR["<b>create_output_dir()</b><br/><i>src/utils.py</i><br/>Creates outputs/lora/{tag}_{ts}/"]
    end

    subgraph PEFT_LIB["<b>🔗 peft library</b>"]
        LORA_CFG["<b>LoraConfig()</b><br/>r=16, alpha=32<br/>targets: q,k,v,o_proj"]
        GET_PEFT["<b>get_peft_model()</b><br/>Wraps model with LoRA layers<br/>Freezes 8B params<br/>Adds 13.6M trainable params"]
    end

    subgraph HF_LIB["<b>🤗 transformers library</b>"]
        TRAIN_ARGS["<b>TrainingArguments()</b><br/>lr=5e-5, epochs=3<br/>batch=2, grad_accum=4<br/>fp16=False (MPS safe)"]
        AUTO_MODEL["<b>AutoModelForCausalLM</b><br/>.from_pretrained()"]
        AUTO_TOK["<b>AutoTokenizer</b><br/>.from_pretrained()"]
    end

    subgraph TRL_LIB["<b>🏋️ trl library</b>"]
        SFT["<b>SFTTrainer()</b><br/>Supervised Finetuning Trainer<br/>Handles the entire training loop"]
        SFT_TRAIN["<b>.train()</b><br/>Forward → Loss → Backward → Update<br/>375 steps × 3 epochs"]
        SFT_SAVE["<b>.save_model()</b><br/>Saves only the LoRA adapter<br/>~55MB (not the 16GB base)"]
    end

    CLI["⌨️ python scripts/train.py<br/>--recipe llama31_sql_lora.yaml"]

    CLI --> RECIPE
    RECIPE --> TOKENIZER
    RECIPE --> MODEL_LOAD
    RECIPE --> DATA_PREP
    RECIPE --> OUT_DIR

    MODEL_LOAD -.->|"calls internally"| AUTO_MODEL
    TOKENIZER -.->|"calls internally"| AUTO_TOK

    DATA_PREP --> SQL_FMT
    SQL_FMT -.->|"uses tokenizer's<br/>chat template"| AUTO_TOK

    MODEL_LOAD --> GET_PEFT
    LORA_CFG --> GET_PEFT

    GET_PEFT --> SFT
    SQL_FMT --> SFT
    TRAIN_ARGS --> SFT
    AUTO_TOK --> SFT

    SFT --> SFT_TRAIN
    SFT_TRAIN --> SFT_SAVE

    SFT_SAVE --> ADAPTER["💾 adapter_model.safetensors<br/>~55MB LoRA weights"]

    style US fill:#0d2818,stroke:#3fb950,stroke-width:2
    style PEFT_LIB fill:#1a0d2e,stroke:#bc8cff,stroke-width:2
    style HF_LIB fill:#0d1a2e,stroke:#58a6ff,stroke-width:2
    style TRL_LIB fill:#2e0d0d,stroke:#f85149,stroke-width:2
    style ADAPTER fill:#1a1a2e,stroke:#3fb950,stroke-width:2
    style CLI fill:#1a1a2e,stroke:#d29922,stroke-width:2
</div>
</div>

<!-- ========================================== -->
<!-- SECTION 2: FUNCTION DETAIL                -->
<!-- ========================================== -->
<h2 id="training-detail">② Key Functions — What Each Step Actually Does</h2>

<h3>Step A: Data Formatting — <code>_format_sql_to_chat()</code></h3>
<div class="callout orange">
    <strong class="orange">This is the most important function for understanding results.</strong>
    It defines exactly what the model sees during training — input AND expected output.
    The format of this training data directly determines what the finetuned model learns to produce.
</div>

<div class="two-col">
    <div>
        <div class="col-label">Raw Dataset (from HuggingFace)</div>
<pre><code>{
  "context": "CREATE TABLE employees (id INT, name VARCHAR, salary FLOAT)",
  "question": "What employees earn over 80000?",
  "answer": "SELECT name FROM employees WHERE salary > 80000"
}</code></pre>
    </div>
    <div>
        <div class="col-label">After _format_sql_to_chat() → using Llama's chat template</div>
<pre><code>&lt;|begin_of_text|&gt;
&lt;|start_header_id|&gt;user&lt;|end_header_id|&gt;

Given the following SQL table schema:

CREATE TABLE employees (id INT, name VARCHAR, salary FLOAT)

Write a SQL query to answer: What employees earn over 80000?
&lt;|eot_id|&gt;
&lt;|start_header_id|&gt;assistant&lt;|end_header_id|&gt;

SELECT name FROM employees WHERE salary > 80000
&lt;|eot_id|&gt;</code></pre>
    </div>
</div>

<div class="callout purple">
    <strong class="purple">Notice:</strong> The assistant's response in the training data is <em>just the SQL</em>.
    No explanation, no markdown, no "here's how it works." The model sees 1000 examples where the
    correct response is always <em>only the SQL query</em>. That's what it learns to produce.
</div>

<h3>Step B: LoRA Wrapping — <code>get_peft_model()</code></h3>
<div class="card">
<div class="mermaid">
graph LR
    subgraph BEFORE["Before get_peft_model()"]
        L1["q_proj<br/>4096×4096<br/>= 16.7M params<br/>✅ trainable"]
        L2["k_proj<br/>4096×1024<br/>= 4.2M params<br/>✅ trainable"]
        L3["v_proj<br/>4096×1024<br/>= 4.2M params<br/>✅ trainable"]
        L4["o_proj<br/>4096×4096<br/>= 16.7M params<br/>✅ trainable"]
        L5["All other layers<br/>~8B params<br/>✅ trainable"]
    end

    subgraph AFTER["After get_peft_model()"]
        A1["q_proj ❄️ FROZEN<br/>+ LoRA A: 4096→16<br/>+ LoRA B: 16→4096<br/>added: 131K params ✅"]
        A2["k_proj ❄️ FROZEN<br/>+ LoRA A: 4096→16<br/>+ LoRA B: 16→1024<br/>added: 82K params ✅"]
        A3["v_proj ❄️ FROZEN<br/>+ LoRA A: 4096→16<br/>+ LoRA B: 16→1024<br/>added: 82K params ✅"]
        A4["o_proj ❄️ FROZEN<br/>+ LoRA A: 4096→16<br/>+ LoRA B: 16→4096<br/>added: 131K params ✅"]
        A5["All other layers<br/>❄️ FROZEN<br/>No LoRA added"]
    end

    BEFORE -->|"getpeftmodel()"| AFTER

    style BEFORE fill:#1a1a2e,stroke:#f85149
    style AFTER fill:#1a1a2e,stroke:#3fb950
</div>
<div class="callout green">
    <strong class="green">Result:</strong> 8B params frozen (unchanged) + 13.6M new LoRA params trainable.
    Only <strong>0.17%</strong> of the model is being trained. The optimizer only stores gradients
    for these 13.6M params — that's why LoRA uses so much less memory than full finetuning.
</div>
</div>

<h3>Step C: Training Loop — What <code>SFTTrainer.train()</code> Does Internally</h3>
<div class="card">
<div class="mermaid">
graph TB
    subgraph LOOP["Training Loop — Repeats 375 times (125 steps × 3 epochs)"]
        direction TB

        BATCH["📦 <b>Get Batch</b><br/>Pick 2 formatted examples<br/>Tokenize → input_ids + labels"]

        FWD["🔄 <b>Forward Pass</b><br/>Input flows through frozen base weights<br/>+ LoRA corrections at q,k,v,o_proj<br/>→ Produces logits (predictions for next token)"]

        LOSS["📉 <b>Compute Loss</b><br/>Cross-entropy between predicted tokens<br/>and the actual SQL answer tokens<br/>(losses on user prompt are masked out)"]

        BWD["⬅️ <b>Backward Pass</b><br/>Compute gradients for LoRA params ONLY<br/>Frozen base weights have no gradients"]

        CLIP["✂️ <b>Gradient Clipping</b><br/>max_grad_norm=0.3<br/>Prevents gradient explosion"]

        UPDATE["🔧 <b>Optimizer Step</b> (AdamW)<br/>Update only the 13.6M LoRA params<br/>Using learning rate from cosine schedule"]

        LOG["📊 <b>Log</b> (every 10 steps)<br/>loss, grad_norm, token_accuracy"]

        BATCH --> FWD --> LOSS --> BWD --> CLIP --> UPDATE --> LOG
        LOG -.->|"next batch"| BATCH
    end

    style LOOP fill:#0d1117,stroke:#f85149,stroke-width:2
</div>
</div>

<div class="callout blue">
    <strong class="blue">Key detail — loss masking:</strong> The loss is computed <em>only on the assistant's response tokens</em>
    (the SQL), not on the user's prompt (the schema + question). The model is penalized for wrong SQL tokens,
    not for failing to reproduce the prompt. This is how SFTTrainer differs from naive next-token training.
</div>

<!-- ========================================== -->
<!-- SECTION 3: INFERENCE FLOW                  -->
<!-- ========================================== -->
<h2 id="inference-flow">③ Inference Flow — Base vs Base+LoRA</h2>

<div class="callout blue">
    <strong class="blue">What happens when you run inference.py:</strong> The same prompt goes through
    both models. The <code>generate()</code> function wraps the prompt in Llama's chat template
    (as a "user" message), then calls <code>model.generate()</code> to produce tokens auto-regressively.
</div>

<div class="card">
<div class="mermaid">
graph TB
    subgraph INPUT["Input - same for both models"]
        PROMPT["Users prompt:<br/>Given CREATE TABLE employees...<br/>Write a SQL query to answer: ..."]
        FMT["format_chat_prompt<br/>Wraps as user message<br/>Applies Llama chat template<br/>Adds generation prompt tag"]
        TOKENS["Tokenized input_ids<br/>Moved to MPS device"]

        PROMPT --> FMT --> TOKENS
    end

    subgraph BASE_PATH["Base Model Path"]
        BASE_MODEL["Llama 3.1 8B Instruct<br/>Original weights - instruction-tuned<br/>Trained on millions of instruction pairs<br/>Default behavior: be helpful + verbose"]
        BASE_GEN["model.generate<br/>Autoregressive: pick next token<br/>feed back, repeat 256 times<br/>temperature=0.7 sampling"]
        BASE_OUT["Output:<br/>To answer this question you can<br/>use the following SQL query:<br/>SELECT name FROM ...<br/>This query works as follows..."]

        BASE_MODEL --> BASE_GEN --> BASE_OUT
    end

    subgraph LORA_PATH["Base + LoRA Path"]
        LORA_MODEL["Llama 3.1 8B Instruct<br/>Same base weights FROZEN<br/>+ LoRA adapter loaded on top<br/>PeftModel wraps the base model"]
        LORA_DETAIL["At each q,k,v,o_proj layer:<br/>output = Wx + BAx<br/>The BAx correction<br/>steers the generation"]
        LORA_GEN["model.generate<br/>Same autoregressive process<br/>But attention is slightly different<br/>due to LoRA corrections"]
        LORA_OUT["Output:<br/>SELECT name FROM employees<br/>WHERE department = Engineering<br/>AND salary greater than 80000"]

        LORA_MODEL --> LORA_DETAIL --> LORA_GEN --> LORA_OUT
    end

    TOKENS --> BASE_MODEL
    TOKENS --> LORA_MODEL

    style INPUT fill:#1a1a2e,stroke:#d29922,stroke-width:2
    style BASE_PATH fill:#0d2818,stroke:#3fb950,stroke-width:2
    style LORA_PATH fill:#1a0d2e,stroke:#bc8cff,stroke-width:2
</div>
</div>

<div class="callout green">
    <strong class="green">Same input, different output.</strong> Both models receive the exact same
    tokenized prompt. The <em>only</em> difference is the tiny LoRA correction (<code>B·A·x</code>)
    at each attention layer. This correction is enough to change the model's behavior from
    "be helpful teacher" to "be SQL engine."
</div>

<!-- ========================================== -->
<!-- SECTION 4: THE REAL DELTA                  -->
<!-- ========================================== -->
<h2 id="real-delta">④ The Real Delta — Finetuning vs Just Asking Nicely</h2>

<div class="callout red">
    <strong class="red">The key question:</strong> "If I just told the base model to <em>only output SQL,
    no explanation</em>, wouldn't it do the same thing? Why bother finetuning?"
</div>

<h3>Test: What if you prompt-engineered the base model?</h3>
<div class="two-col">
    <div class="delta-col base">
        <div class="col-label" style="color: var(--green);">Base Model with Strict Prompt</div>
<pre><code>"Given the following SQL table schema:

CREATE TABLE employees (...)

Write a SQL query to answer: ...

<b>IMPORTANT: Output ONLY the raw SQL query.
No explanation, no markdown, no code blocks.
Just the SQL.</b>"</code></pre>
        <p style="margin-top:1rem; color: var(--text-muted); font-size: 0.9rem;">
            <strong>Likely result:</strong> The base model would mostly comply — it's instruction-tuned,
            so it follows instructions. You'd get SQL with maybe occasional slip-ups
            (adding a semicolon explanation, or "Here's the query:" prefix).
        </p>
        <p style="margin-top: 0.5rem; color: var(--orange); font-size: 0.9rem;">
            ⚠️ <strong>But:</strong> You need this extra instruction <em>every single time</em>.
            It's prompt engineering — fragile, adds tokens, and the model may still "break character."
        </p>
    </div>
    <div class="delta-col lora" style="margin-left: 1.5rem;">
        <div class="col-label" style="color: var(--purple);">Finetuned Model (no special instructions)</div>
<pre><code>"Given the following SQL table schema:

CREATE TABLE employees (...)

Write a SQL query to answer: ..."</code></pre>
        <p style="margin-top:1rem; color: var(--text-muted); font-size: 0.9rem;">
            <strong>Result:</strong> The finetuned model outputs just SQL — <em>without</em> being told to.
            The format is baked into the weights. No extra prompt engineering needed.
        </p>
        <p style="margin-top: 0.5rem; color: var(--green); font-size: 0.9rem;">
            ✅ <strong>Why this matters:</strong> The behavior is <em>reliable, consistent, and automatic</em>.
            You get the same format every time because the weights learned it.
        </p>
    </div>
</div>

<h3 style="margin-top: 2rem;">The Three Levels of Delta</h3>
<div class="card">
<table style="width: 100%; border-collapse: collapse;">
    <thead>
        <tr>
            <th style="text-align:left; padding:0.75rem; border-bottom:2px solid var(--border); color: var(--text-muted); font-size: 0.85rem;">WHAT</th>
            <th style="text-align:left; padding:0.75rem; border-bottom:2px solid var(--border); color: var(--text-muted); font-size: 0.85rem;">PROMPT ENGINEERING</th>
            <th style="text-align:left; padding:0.75rem; border-bottom:2px solid var(--border); color: var(--text-muted); font-size: 0.85rem;">FINETUNING</th>
            <th style="text-align:left; padding:0.75rem; border-bottom:2px solid var(--border); color: var(--text-muted); font-size: 0.85rem;">WHERE THE DELTA GETS BIGGER</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); font-weight:600;">1. Format</td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--orange);">
                "Output only SQL" — works ~90% of the time
            </td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--green);">
                Always outputs SQL — baked into weights
            </td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--text-muted);">
                Small delta — format is easy for LLMs
            </td>
        </tr>
        <tr>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); font-weight:600;">2. Domain knowledge</td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--orange);">
                Only what's in the model's pretraining data
            </td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--green);">
                Can teach new SQL patterns, dialect-specific syntax
            </td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--text-muted);">
                Big delta — especially for proprietary schemas
            </td>
        </tr>
        <tr>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); font-weight:600;">3. Reliability at scale</td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--orange);">
                Each API call costs prompt tokens<br/>
                Inconsistent behavior across calls
            </td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--green);">
                Deterministic behavior, no prompt overhead<br/>
                Deploy as service, consistent output
            </td>
            <td style="padding:0.75rem; border-bottom:1px solid var(--border); color:var(--text-muted);">
                Huge delta — at 1000s of calls
            </td>
        </tr>
        <tr>
            <td style="padding:0.75rem; font-weight:600;">4. Cost at production</td>
            <td style="padding:0.75rem; color:var(--orange);">
                Long prompts = more tokens = more $<br/>
                System prompt repeated every call
            </td>
            <td style="padding:0.75rem; color:var(--green);">
                Short prompt (just schema + question)<br/>
                Behavior built-in, not prompted
            </td>
            <td style="padding:0.75rem; color:var(--text-muted);">
                Massive delta at production scale
            </td>
        </tr>
    </tbody>
</table>
</div>

<h3>When Finetuning Really Shines vs When Prompting Is Enough</h3>
<div class="two-col">
    <div class="card">
        <h3 style="color: var(--orange);">Prompting is enough when...</h3>
        <ul style="margin-left: 1rem; line-height: 2;">
            <li>You need general SQL (standard syntax)</li>
            <li>Low volume (dozens of queries/day)</li>
            <li>Format doesn't matter much</li>
            <li>You have room for long system prompts</li>
            <li>The base model already "knows" the domain</li>
        </ul>
    </div>
    <div class="card">
        <h3 style="color: var(--green);">Finetuning shines when...</h3>
        <ul style="margin-left: 1rem; line-height: 2;">
            <li>Proprietary schema, custom SQL dialect</li>
            <li>High volume (1000s of queries/day)</li>
            <li>Strict output format required (API integration)</li>
            <li>You can't afford prompt token overhead</li>
            <li>You're teaching behaviors NOT in pretraining</li>
        </ul>
    </div>
</div>

<h3 style="margin-top: 2rem;">What Our Experiment Proved</h3>
<div class="callout blue">
    <strong class="blue">With just 1000 examples and 25 minutes of MPS training, the model learned:</strong><br/>
    <br/>
    ✅ <strong>Format shift</strong> — Outputs raw SQL (no markdown, no explanation)<br/>
    ✅ <strong>Schema parsing</strong> — Correctly reads CREATE TABLE → maps to SELECT columns<br/>
    ✅ <strong>Concise by default</strong> — Doesn't need "only output SQL" instruction<br/>
    <br/>
    The SQL is functionally equivalent to the base model's SQL — so for <em>this specific dataset</em>,
    the main delta is format and reliability. For a proprietary dataset (your company's specific
    tables, naming conventions, joins), the delta would be much larger because the base model
    has never seen those schemas.
</div>

<script>
mermaid.initialize({
    theme: 'dark',
    themeVariables: {
        primaryColor: '#1a1a2e',
        primaryTextColor: '#e6edf3',
        primaryBorderColor: '#58a6ff',
        lineColor: '#30363d',
        secondaryColor: '#161b22',
        tertiaryColor: '#0d1117'
    },
    flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis'
    }
});
</script>
</body>
</html>"""


def main():
    html = build_html()
    out_dir = Path("learning/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "flow_diagrams.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"✓ Flow diagrams generated: {out_path}")
    print(f"  Open in browser: open {out_path}")


if __name__ == "__main__":
    main()
