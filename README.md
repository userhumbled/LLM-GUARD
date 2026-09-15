<div align="center">

# LLM GUARD

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Gradio UI](https://img.shields.io/badge/Gradio-UI-orange.svg)](https://gradio.app/)
[![Engine](https://img.shields.io/badge/Models-DeBERTa--v3%20%7C%20Toxic--BERT-teal.svg)](https://huggingface.co/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
</div>
<div align="left">

Prompt security guard that scans user inputs for **prompt injection / jailbreak attacks**  and **psychological toxicity**  before they reach your LLM. Includes a multi-layer deobfuscation engine and professional prompt analysis. 85% accuracy on public prompt tests.

Runs on any machine with CPU, CUDA, or Apple MPS. Server or laptop, local or cloud

</div>

## Startup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/prompp.git
cd prompp/v3
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Run the guard server:
```bash
python guard_server.py
```


---

## Overview

- **Anti-cipher:** Can detect and translate NFKD unicode; unpacks Base64, Hex, Binary, ROT13, Leetspeak.

- **Injection Model:** Evaluates protectai/deberta-v3-base-prompt-injection with softmax probabilities.
- **Strided Chunking:** Defeats truncation attacks via 512-token windows with 256-token overlap.
- **Toxicity Scoring:** Runs unitary/toxic-bert using 6-head multi-label outputs.
- **Heuristic Risk Fusion:** Lowers injection thresholds automatically when hidden payloads unpack.
- **Universal Hardware Backend:** Native PyTorch inference across CUDA, MPS, and CPU.

---

