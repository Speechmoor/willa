#!/usr/bin/env python3
"""Attention inside Willa's translation model — PE2.

    python scripts/eval_attention.py
    python scripts/eval_attention.py --sentence "Your own text here"

PE2 built one attention head by hand: an embedding matrix in, Q/K/V out,
scaled dot-product attention, softmax, then add-and-norm. This runs the same
sequence of operations inside NLLB-200 — the model that actually produces
Willa's translated letters — and prints the intermediate shapes so each stage
of PE2 can be pointed at something real.

It exists for one specific reason. Willa has an observed failure in which
"plaintiff" round-trips to "defendant" in isiZulu. That is an attention-level
phenomenon: the model must decide which noun a role attaches to, and if the
attention over the source sentence puts weight on the wrong participant, the
output is fluent and wrong. This makes that decision inspectable rather than
a matter of assertion.

Requires transformers and torch, which are already needed for translation:
    python scripts/fetch_translator.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402

BAR = "=" * 74

# A sentence in which two people hold opposite legal roles. If attention
# blurs them, the translation swaps who owes whom.
DEFAULT = ("The plaintiff Thandi Mokoena claims R4750 from the defendant "
           "Blue Sky Appliances.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sentence", default=DEFAULT)
    ap.add_argument("--target", default="zul_Latn",
                    help="FLORES code for the output language")
    args = ap.parse_args()

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    except ImportError:
        print("  transformers/torch not installed.")
        print("  pip install transformers torch  (or run scripts/fetch_translator.py)")
        return 1

    src = config.NLLB_LOCAL_DIR
    if not Path(src).exists():
        print(f"  Model not found at {src}")
        print("  Run: python scripts/fetch_translator.py")
        return 1

    print(BAR)
    print("PE2 — ATTENTION IN THE TRANSLATION MODEL")
    print(BAR)
    print(f"  model:    {config.NLLB_MODEL}")
    print(f"  sentence: {args.sentence}\n")

    tok = AutoTokenizer.from_pretrained(str(src), src_lang="eng_Latn")
    model = AutoModelForSeq2SeqLM.from_pretrained(str(src))
    model.eval()

    enc = tok(args.sentence, return_tensors="pt")
    ids = enc["input_ids"][0]
    pieces = tok.convert_ids_to_tokens(ids)

    # ---- PE2 Section B: the input embedding matrix -----------------------
    print(BAR)
    print("B. INPUT EMBEDDINGS")
    print(BAR)
    emb_layer = model.get_input_embeddings()
    X = emb_layer(enc["input_ids"])
    print(f"  tokens ({len(pieces)}): {pieces}")
    print(f"\n  embedding matrix for this sentence: {tuple(X.shape)}")
    print(f"    batch {X.shape[0]}, sequence {X.shape[1]}, model dim {X.shape[2]}")
    print(f"  full vocabulary embedding table: {tuple(emb_layer.weight.shape)}")
    print("\n  PE2 built this by hand as a small matrix of made-up numbers.")
    print("  Same object, learned: one row per token, d_model columns.")

    # ---- PE2 Section C: Q, K, V ------------------------------------------
    print("\n" + BAR)
    print("C. Q, K AND V")
    print(BAR)
    attn = model.model.encoder.layers[0].self_attn
    d_model = X.shape[-1]
    heads = attn.num_heads
    d_head = d_model // heads

    Q = attn.q_proj(X)
    K = attn.k_proj(X)
    V = attn.v_proj(X)
    print(f"  q_proj / k_proj / v_proj are learned linear maps of "
          f"{tuple(attn.q_proj.weight.shape)}")
    print(f"  Q: {tuple(Q.shape)}   K: {tuple(K.shape)}   V: {tuple(V.shape)}")
    print(f"\n  heads: {heads}, so each head sees d_head = {d_model}/{heads} "
          f"= {d_head}")
    print("  PE2 computed one head; a real encoder layer runs all of them in")
    print("  parallel and concatenates, which is why d_head divides d_model.")

    # ---- PE2 Section D: scaled dot-product attention ---------------------
    print("\n" + BAR)
    print("D. SCALED DOT-PRODUCT ATTENTION")
    print(BAR)
    import math
    q1 = Q[0].view(-1, heads, d_head).transpose(0, 1)   # (heads, seq, d_head)
    k1 = K[0].view(-1, heads, d_head).transpose(0, 1)
    scores = q1 @ k1.transpose(-1, -2)
    scaled = scores / math.sqrt(d_head)
    weights = torch.softmax(scaled, dim=-1)

    print(f"  QK^T:            {tuple(scores.shape)}  "
          f"(heads, seq, seq)")
    print(f"  raw score range: {scores.min():.2f} to {scores.max():.2f}")
    print(f"  after / sqrt({d_head}): {scaled.min():.2f} to {scaled.max():.2f}")
    print("\n  The division is the whole reason PE2 separates these two steps.")
    print("  Dot products grow with d_head, and large magnitudes drive softmax")
    print("  toward one-hot — a head that attends to exactly one token and")
    print("  passes almost no gradient. Scaling keeps the distribution usable.")
    print(f"\n  after softmax:   rows sum to "
          f"{weights[0].sum(dim=-1).mean():.4f} (should be 1.0)")

    # ---- the part that matters for Willa ---------------------------------
    print("\n" + BAR)
    print("WHERE 'PLAINTIFF' AND 'DEFENDANT' ATTEND")
    print(BAR)
    avg = weights.mean(dim=0)          # average over heads
    interesting = [i for i, p in enumerate(pieces)
                   if any(w in p.lower() for w in
                          ("plaintiff", "defendant", "claim", "from"))]
    if not interesting:
        interesting = list(range(min(6, len(pieces))))

    for i in interesting:
        row = avg[i]
        top = torch.topk(row, min(5, len(pieces)))
        tops = ", ".join(f"{pieces[j]}({row[j]:.2f})"
                         for j in top.indices.tolist())
        print(f"  {pieces[i]:>14} attends to: {tops}")

    print("\n  Read this against the isiZulu failure. The roles in this")
    print("  sentence are carried by word order and by two English function")
    print("  words. If a head does not bind 'plaintiff' to Mokoena and")
    print("  'defendant' to Blue Sky, nothing downstream can recover it, and")
    print("  the translation names the wrong party as owing the money while")
    print("  reading perfectly well.")

    # ---- PE2 Section E: add and norm -------------------------------------
    print("\n" + BAR)
    print("E. ADD AND NORM")
    print(BAR)
    ctx = (weights @ V[0].view(-1, heads, d_head).transpose(0, 1))
    ctx = ctx.transpose(0, 1).reshape(1, -1, d_model)
    out = attn.out_proj(ctx)
    residual = X + out
    normed = model.model.encoder.layers[0].self_attn_layer_norm(residual)

    print(f"  attention output:  {tuple(out.shape)}")
    print(f"  X + attention:     {tuple(residual.shape)}   "
          f"sd {residual.std():.3f}")
    print(f"  after layer norm:  {tuple(normed.shape)}   "
          f"mean {normed.mean():.4f}, sd {normed.std():.3f}")
    print("\n  The residual add is why depth does not destroy the signal: the")
    print("  original embedding survives every layer. The norm is why the")
    print("  scale stays comparable across layers — mean near 0, sd near 1,")
    print("  exactly as PE2's Section E computed by hand.")

    print(f"\n  encoder layers in this model: "
          f"{len(model.model.encoder.layers)}")
    print("  Everything above is one of them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
