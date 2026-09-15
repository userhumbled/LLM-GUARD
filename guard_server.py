import os
import sys
import time
import gradio as gr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deobfuscator import Deobfuscator
from deberta_tox_models import DebertaToxEngine


class GuardPipeline:
    def __init__(self):
        self.deobfuscator = Deobfuscator()
        self.engine = DebertaToxEngine()

    def evaluate_prompt(
        self,
        prompt: str,
        tech_thresh: float,
        hate_thresh: float,
        threat_thresh: float,
        toxic_thresh: float,
    ) -> tuple:
        t0 = time.perf_counter()
        prep_data = self.deobfuscator.deobfuscate_prompt(prompt)

        primary_text = prep_data["inspected_text"]
        leet_text = prep_data["leet_normalized"]

        tech_score = self.engine.eval_deberta_injection(primary_text)
        if leet_text != primary_text:
            alt_score = self.engine.eval_deberta_injection(leet_text)
            if alt_score > tech_score:
                tech_score = alt_score

        tox_scores = self.engine.eval_toxic_bert(primary_text)
        latency = (time.perf_counter() - t0) * 1000

        is_tech_harm = (
            tech_score >= tech_thresh
            or (len(prep_data["obfuscations_found"]) > 0 and tech_score >= 0.50)
        )
        is_hate_harm = tox_scores["identity_hate"] >= hate_thresh
        is_threat_harm = tox_scores["threat"] >= threat_thresh
        is_toxic_harm = (
            tox_scores["severe_toxic"] >= toxic_thresh
            or tox_scores["toxic"] >= toxic_thresh
        )

        is_psych_harm = is_hate_harm or is_threat_harm or is_toxic_harm

        if is_tech_harm and is_psych_harm:
            decision = "HARMFUL (CRITICAL VIOLATION: TECHNICAL & PSYCHOLOGICAL)"
            border_col = "#ef4444"
            bg = "#450a0a"
            summary = "Prompt violates both system integrity and behavioral toxicity policies."
        elif is_tech_harm:
            decision = "HARMFUL (TECHNICAL THREAT DETECTED)"
            border_col = "#f97316"
            bg = "#431407"
            summary = "Control-flow manipulation, jailbreak, or obfuscated injection detected."
        elif is_psych_harm:
            decision = "HARMFUL (PSYCHOLOGICAL / TOXICITY DETECTED)"
            border_col = "#ef4444"
            bg = "#450a0a"
            summary = "Hate speech, violent threat, harassment, or self-harm content identified."
        elif (
            tech_score >= 0.5
            or tox_scores["identity_hate"] >= 0.3
            or tox_scores["threat"] >= 0.3
        ):
            decision = "SUSPICIOUS (BORDERLINE CONTENT)"
            border_col = "#eab308"
            bg = "#422006"
            summary = "Elevated risk scores observed across one or more evaluation axes."
        else:
            decision = "NOT HARMFUL (SAFE / HEALTHY)"
            border_col = "#22c55e"
            bg = "#052e16"
            summary = "No injection, jailbreak, obfuscated exploit, or toxic patterns found."

        banner_html = f"""
        <div style="background-color: {bg}; border: 2px solid {border_col}; border-radius: 8px; padding: 18px; margin-bottom: 15px;">
            <h2 style="color: {border_col}; margin: 0 0 6px 0; font-size: 20px;">{decision}</h2>
            <p style="color: #e5e7eb; margin: 0; font-size: 14px;"><strong>Diagnosis:</strong> {summary} | <strong>Latency:</strong> {latency:.2f} ms</p>
        </div>
        """

        tech_report = {
            "Prompt Injection Probability": f"{tech_score:.4f}",
            "Technical Threshold": f"{tech_thresh:.2f}",
            "Technical State": "FLAGGED" if is_tech_harm else "CLEAN",
            "Obfuscated Payloads Extracted": prep_data["obfuscations_found"],
            "Ciphers/Encodings Discovered": len(prep_data["obfuscations_found"]) > 0,
            "Evaluated Target Length": len(primary_text),
        }

        psych_report = {
            "Hate Speech (Identity Hate)": f"{tox_scores['identity_hate']:.4f}",
            "Physical Threat / Self-Harm": f"{tox_scores['threat']:.4f}",
            "Severe Hostility / Abuse": f"{tox_scores['severe_toxic']:.4f}",
            "General Toxicity": f"{tox_scores['toxic']:.4f}",
            "Insult Level": f"{tox_scores['insult']:.4f}",
            "Obscene / Vulgarity": f"{tox_scores['obscene']:.4f}",
            "Psychological State": "FLAGGED" if is_psych_harm else "CLEAN",
        }

        return banner_html, tech_report, psych_report


pipeline_instance = None


def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        pipeline_instance = GuardPipeline()
    return pipeline_instance


def analyze_input(text, tech_th, hate_th, threat_th, tox_th):
    pipe = get_pipeline()
    return pipe.evaluate_prompt(text, tech_th, hate_th, threat_th, tox_th)


def build_guard_interface():
    with gr.Blocks(title="LLM GUARD", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# LLM GUARD")

        with gr.Row():
            with gr.Column(scale=4):
                input_box = gr.Textbox(
                    lines=5,
                    placeholder="Submit text for pre-flight multi-layer inspection...",
                    label="Raw User Prompt",
                )
                with gr.Row():
                    run_btn = gr.Button("Inspect Input", variant="primary")
                    clear_btn = gr.ClearButton(components=[input_box])

            with gr.Column(scale=3):
                gr.Markdown("### Threshold Tuning")
                tech_s = gr.Slider(
                    0.30, 0.99, value=0.80, step=0.01, label="Technical Threshold"
                )
                hate_s = gr.Slider(
                    0.20, 0.95, value=0.50, step=0.01, label="Hate Speech Threshold"
                )
                threat_s = gr.Slider(
                    0.20, 0.95, value=0.50, step=0.01, label="Threat / Harm Threshold"
                )
                tox_s = gr.Slider(
                    0.20, 0.95, value=0.65, step=0.01, label="Toxicity Threshold"
                )

        gr.Markdown("### Concluding Verdict")
        decision_banner = gr.HTML()

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Technical Threat")
                tech_output = gr.JSON(label="System Security & Injections")
            with gr.Column():
                gr.Markdown("### Psychological / Toxicity Level")
                psych_output = gr.JSON(label="Behavioral Harm & Hate Speech")

        run_btn.click(
            fn=analyze_input,
            inputs=[input_box, tech_s, hate_s, threat_s, tox_s],
            outputs=[decision_banner, tech_output, psych_output],
        )
    return demo


def start_server():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "7860"))
    share = os.environ.get("SHARE", "False").lower() in ("true", "1")
    interface = build_guard_interface()
    interface.launch(server_name=host, server_port=port, share=share)


if __name__ == "__main__":
    start_server()
