"""
Fine-tuning pipeline for Llama-3-8B on annotated planning dialogues.

Could change in the future:
Uses LoRA (via PEFT) for parameter-efficient fine-tuning.
Only needed if prompt engineering alone fails to reliably elicit implicit
assumptions or produce well-formed graph updates.

Target hardware: single GPU on instgpu-{01..05}.cs.wisc.edu
"""

# TODO: implement (only if prompt engineering proves insufficient)
