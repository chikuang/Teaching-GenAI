"""Render the course's original workflow diagrams for HTML, notebooks, and PDF.

Run with the course Python environment. Checked-in PNGs keep Sphinx builds
independent of browser JavaScript or a separate diagram renderer.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "_static" / "diagrams"
DIAGRAMS = {
    "01-statistical-workflow": ("Fit, simulate, and evaluate different objects", [
        ("ESTIMATION", ["Observed training\ndata", "Counts and\nsmoothing", "Fitted probability\ndistribution"]),
        ("SIMULATION", ["Hold fitted model\nfixed", "Draw new random\nsamples", "Check Monte Carlo\napproximation"]),
        ("EVALUATION", ["Held-out observed\ndata", "Score with the\nfitted model", "Compare predictive\nlosses"]),
    ], "More simulated draws improve Monte Carlo precision, not the fitted model."),
    "02-neural-training": ("A neural-network experiment has two loops", [
        ("TRAINING LOOP", ["Training\nminibatch", "Forward loss +\nbackward gradient", "Optimizer step;\nrepeat on batches"]),
        ("MODEL SELECTION", ["Validation loss\nacross checkpoints", "Select and freeze\none checkpoint", "One final test\nagainst baselines"]),
    ], "Validation selects the checkpoint. The test set does not choose it."),
    "03-representation": ("Learn representations, then reuse the fitted objects", [
        ("LEARN ON TRAINING TEXT", ["Corpus and\nnormalization", "Tokenizer, vocabulary,\nand token IDs", "Embedding table\nor co-occurrence fit"]),
        ("ENCODE NEW TEXT", ["Apply frozen\ntokenizer", "Look up embeddings\nand add positions", "Contextual model\nuses the sequence"]),
    ], "Unknown-token handling and the tokenizer version are part of the model."),
    "04-attention": ("Attention is a sequence of matrix operations", [
        ("ONE HEAD", ["Project inputs\nto Q, K, V", "Scale QK transpose;\napply allowed mask", "Row softmax A;\noutput A times V"]),
        ("MULTIPLE HEADS", ["Repeat with separate\nprojection weights", "Concatenate\nhead outputs", "Output projection\nto model width"]),
    ], "Rows are query positions. A causal mask removes future keys before softmax."),
    "05-transformer": ("A pre-normalized decoder: blocks, then probabilities", [
        ("INSIDE EACH BLOCK", ["States -> layer norm\n-> causal attention", "Add residual; normalize\n-> feed-forward net", "Add second residual;\npass to next block"]),
        ("WHOLE MODEL", ["Token embeddings\n+ positions", "Repeat decoder blocks\n-> final layer norm", "Linear vocabulary head\n-> logits / softmax"]),
    ], "Residual additions preserve width. The vocabulary head changes the final dimension."),
    "06-language-model": ("Training estimates a model; decoding uses it", [
        ("TRAIN AND SELECT", ["Input prefixes +\nshifted token targets", "Minimize token NLL;\ncheck validation loss", "Freeze selected\nmodel parameters"]),
        ("AUTOREGRESSIVE LOOP", ["Prompt + tokens\ngenerated so far", "Predict next-token\nprobabilities", "Decode and append;\nrepeat until stopping"]),
    ], "Temperature, top-k, and nucleus sampling change decoding, not fitted weights."),
    "07-generative-families": ("Three frameworks, three learning objectives", [
        ("VAE", ["Observed x -> encoder\nq(z | x)", "Reparameterized z\n-> decoder p(x | z)", "Reconstruction + KL\noptimize the ELBO"]),
        ("GAN", ["Noise z -> generator\nproduces G(z)", "Discriminator compares\nreal and generated x", "Alternate discriminator\nand generator updates"]),
        ("NORMALIZING FLOW", ["Base z and\ninvertible x = f(z)", "Inverse transform +\nJacobian determinant", "Exact density objective;\nsample by forward map"]),
    ], "Generation uses the VAE prior, the GAN generator, or the flow's forward transform."),
    "08-diffusion": ("Learn denoising, then run a reverse-time chain", [
        ("TRAINING", ["Clean x0 + random t\n+ Gaussian noise", "Construct noisy xt\nwith known schedule", "Predict noise; minimize\nsquared error"]),
        ("GENERATION", ["Initialize xT\nfrom Gaussian noise", "Use fitted denoiser\nfor xt -> x(t-1)", "Repeat reverse steps\nuntil the final x0"]),
    ], "The forward noising schedule is fixed. The reverse denoiser is learned."),
    "09-adaptation": ("Choose the update and the data it requires", [
        ("SUPERVISED FINE-TUNING", ["Prompt-response\ntraining examples", "Token prediction\nloss", "Update chosen\nmodel parameters"]),
        ("LOW-RANK UPDATE", ["Freeze base\nweight W0", "Optimize low-rank\nfactors B and A", "Use W0 + BA\nfor prediction"]),
        ("DIRECT PREFERENCE", ["Preferred / rejected\npairs + reference", "Policy/reference\nlog-ratio objective", "Update policy; assess\nheld-out preferences"]),
    ], "LoRA specifies which updates are allowed; DPO specifies a preference objective."),
    "10-rag-pipeline": ("RAG connects a versioned index to an answer", [
        ("OFFLINE: WHEN SOURCES CHANGE", ["Load and parse\nsource documents", "Chunk text; attach\nIDs and versions", "Encode chunks;\nstore searchable index"]),
        ("ONLINE: RETRIEVE AND AUGMENT", ["Question -> query\nrepresentation", "Retrieve candidates;\noptionally rerank", "Select evidence within\na context budget"]),
        ("ONLINE: GENERATE AND CHECK", ["Question + instructions\n+ identified passages", "Generator returns\nanswer and citations", "Check support;\nanswer or abstain"]),
    ], "The online retriever uses the offline index. Updating documents need not retrain the generator."),
    "10-rag-diagnosis": ("Use controlled comparisons to locate a RAG failure", [
        ("NO RETRIEVAL", ["Question\nonly", "Same model and\ndecoding settings", "Measure answers from\nparametric knowledge"]),
        ("ORACLE EVIDENCE", ["Question + human-\nselected evidence", "Same model and\ndecoding settings", "Diagnose generation\nand support errors"]),
        ("ACTUAL RETRIEVAL", ["Question + passages\nfrom the retriever", "Same model and\ndecoding settings", "Measure end-to-end\nretrieval + generation"]),
    ], "Oracle passages are an evaluation intervention, not information available in deployment."),
    "11-evaluation": ("Separate selection, calibration, and final reporting", [
        ("EXPERIMENT DESIGN", ["Task population,\nloss, and sample unit", "Group-aware split;\ndevelopment choices", "Lock the system\nbefore testing"]),
        ("UNCERTAINTY ANALYSIS", ["Separate probability-fit\nand set-calibration data", "Freeze temperature /\nconformal threshold", "Test metrics + paired\nor cluster uncertainty"]),
    ], "The resampling unit follows dependence. Calibration does not license reuse of the test set."),
    "12-agent-loop": ("A policy proposes; the executor controls actions", [
        ("DECIDE", ["Task + current state\n+ observed evidence", "Policy proposes\na typed action", "Validate tool, arguments,\npermissions, and budget"]),
        ("ACT AND UPDATE", ["Execute approved tool\nor return an error", "Record observation\nand update state", "Stop with a report,\nor return to DECIDE"]),
    ], "A retrieved document can change observations; it cannot grant permission to act."),
    "13-reliability": ("Compare complete agent trajectories on paired tasks", [
        ("RUN THE EXPERIMENT", ["Held-out tasks\nx repeated trials", "Paired policies with\ncontrolled tool failures", "Log outcomes, calls,\ncost, and stop reason"]),
        ("ANALYZE", ["Aggregate repetitions\nwithin each task", "Resample task clusters\nfor paired differences", "Inspect failure types\nand component ablations"]),
    ], "Calls within one task are not independent experiments."),
    "14-capstone": ("Keep numerical evidence independent of generated prose", [
        ("EXECUTION CORE", ["Structured request\n-> schema validation", "Approved simulation\nwith fixed budget", "Estimates + Monte Carlo\nintervals -> report"]),
        ("EVALUATION", ["Locked scenarios\nexcluded from tuning", "Independent high-\nprecision references", "Compare error, failures,\nand computational cost"]),
        ("OPTIONAL LLM LAYER", ["Natural-language task\n-> proposed request", "Same validator and\nstatistical tool", "Evidence-grounded prose;\nverify numeric claims"]),
    ], "Compare the LLM extension with the deterministic core on the same scenarios."),
}


def draw(name, title, lanes, note):
    height = 1.0 + 1.7 * len(lanes)
    fig, ax = plt.subplots(figsize=(10, height))
    fig.patch.set_facecolor("white")
    ax.set(xlim=(0, 10), ylim=(0, height))
    ax.axis("off")
    ax.text(.15, height-.32, title, fontsize=16, weight="bold", color="#243345", va="center")
    ax.plot([.15, 9.85], [height-.61]*2, color="#fed34c", linewidth=3)
    for row, (label, nodes) in enumerate(lanes):
        y = height - 1.68 - row*1.7
        ax.text(.15, y+0.63, label, fontsize=10.5, weight="bold", color="#a2006e", va="bottom")
        for col, text in enumerate(nodes):
            x = .15 + col*3.35
            fill = ["#f5f7f9", "#fff7d4", "#fbeaf5"][col]
            ax.add_patch(FancyBboxPatch((x, y-.5), 2.95, .99, boxstyle="round,pad=0.02,rounding_size=.09", facecolor=fill, edgecolor="#aeb9c6", linewidth=.9))
            ax.text(x+1.475, y, text, ha="center", va="center", fontsize=13.5, color="#243345", linespacing=1.4)
            if col < 2:
                ax.add_patch(FancyArrowPatch((x+2.99, y), (x+3.30, y), arrowstyle="-|>", mutation_scale=15, color="#a2006e", linewidth=1.5))
    ax.text(.15, .15, note, fontsize=10.2, color="#4b5968", va="bottom")
    fig.subplots_adjust(left=.015, right=.985, top=.985, bottom=.015)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT/f"{name}.png", dpi=220, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    for name, (title, lanes, note) in DIAGRAMS.items():
        draw(name, title, lanes, note)
    print(f"Rendered {len(DIAGRAMS)} diagrams in {OUTPUT}")
