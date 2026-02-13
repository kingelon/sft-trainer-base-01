# Model Notes

Running observations on model behaviors, input/output formats, and quirks.

---

## Llama 3.1 8B Instruct

**Model ID**: `meta-llama/Llama-3.1-8B-Instruct`

### Chat Template
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_message}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{assistant_message}<|eot_id|>
```

### Key Observations
- Uses `<|eot_id|>` as turn separator (different from EOS)
- Tokenizer has 128,256 vocab size
- BOS token: `<|begin_of_text|>` (id: 128000)
- EOS token: `<|end_of_text|>` (id: 128001)
- Supports tool calling in chat template
- _Add observations here as you experiment..._

---

## Mistral 7B

**Model IDs**:
- Base: `mistralai/Mistral-7B-v0.1`
- Instruct: `mistralai/Mistral-7B-Instruct-v0.3`

### Chat Template (Instruct)
```
<s>[INST] {user_message} [/INST] {assistant_message}</s>
[INST] {follow_up} [/INST]
```

### Key Observations
- 32,000 vocab size (much smaller than Llama 3.1)
- Uses `[INST]`/`[/INST]` delimiters
- Sliding window attention (4096 tokens)
- No system prompt in original template (v0.1/v0.2), added in v0.3
- _Add observations here as you experiment..._

---

## Comparison Notes

| Aspect | Llama 3.1 8B | Mistral 7B |
|--------|-------------|------------|
| Params | 8B | 7.2B |
| Vocab | 128K | 32K |
| Context | 128K | 32K (sliding window) |
| Chat format | Header-based | `[INST]` tags |
| System prompt | Native support | v0.3 only |
| License | Llama 3.1 Community | Apache 2.0 |

_Add comparative observations here..._
