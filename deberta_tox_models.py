import os
import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def get_compute_device() -> str:
    env_device = os.environ.get("DEVICE", "").strip()
    if env_device:
        return env_device
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_model_path(default_id: str, env_var: str) -> str:
    env_path = os.environ.get(env_var, "").strip()
    if env_path and os.path.exists(env_path):
        return env_path
    slug = default_id.replace("/", "_")
    search_paths = [
        os.path.join(os.getcwd(), "models", slug),
        os.path.join(os.path.dirname(__file__), "..", "models", slug),
        os.path.join(os.path.dirname(__file__), "models", slug),
    ]
    for p in search_paths:
        if os.path.exists(p) and os.path.isdir(p):
            return p
    return default_id


class DebertaToxEngine:
    def __init__(self, device: str = None):
        self.device = device or get_compute_device()

        self.deberta_model_id = resolve_model_path(
            "protectai/deberta-v3-base-prompt-injection-v2",
            "TECH_MODEL_PATH",
        )
        self.deberta_tokenizer = AutoTokenizer.from_pretrained(self.deberta_model_id)
        self.deberta_model = AutoModelForSequenceClassification.from_pretrained(
            self.deberta_model_id
        ).to(self.device)
        self.deberta_model.eval()

        self.toxic_bert_id = resolve_model_path(
            "unitary/toxic-bert",
            "TOX_MODEL_PATH",
        )
        self.toxic_tokenizer = AutoTokenizer.from_pretrained(self.toxic_bert_id)
        self.toxic_model = AutoModelForSequenceClassification.from_pretrained(
            self.toxic_bert_id
        ).to(self.device)
        self.toxic_model.eval()

        self.toxicity_labels = [
            "toxic",
            "severe_toxic",
            "obscene",
            "threat",
            "insult",
            "identity_hate",
        ]

    def eval_deberta_injection(self, text: str) -> float:
        tokens = self.deberta_tokenizer(
            text, return_tensors="pt", add_special_tokens=False
        )["input_ids"][0]

        if len(tokens) <= 450:
            inputs = self.deberta_tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512
            ).to(self.device)
            with torch.no_grad():
                logits = self.deberta_model(**inputs).logits
                probs = F.softmax(logits, dim=-1)[0]
                return probs[1].item()

        max_risk = 0.0
        for i in range(0, len(tokens), 400):
            chunk = tokens[i : i + 450]
            cls_token = torch.tensor([self.deberta_tokenizer.cls_token_id], dtype=torch.long)
            sep_token = torch.tensor([self.deberta_tokenizer.sep_token_id], dtype=torch.long)
            inp = torch.cat([cls_token, chunk, sep_token]).unsqueeze(0).to(self.device)
            mask = torch.ones_like(inp).to(self.device)
            with torch.no_grad():
                logits = self.deberta_model(input_ids=inp, attention_mask=mask).logits
                probs = F.softmax(logits, dim=-1)[0]
                risk = probs[1].item()
                if risk > max_risk:
                    max_risk = risk
            if i + 450 >= len(tokens):
                break
        return max_risk

    def eval_toxic_bert(self, text: str) -> dict:
        inputs = self.toxic_tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        ).to(self.device)
        with torch.no_grad():
            logits = self.toxic_model(**inputs).logits
            probs = torch.sigmoid(logits)[0]

        scores = {}
        for idx, label in enumerate(self.toxicity_labels):
            scores[label] = probs[idx].item()
        return scores
