Yes, exactly. The right way is **iterative**, not one giant redesign. Use the AI coder to implement one phase, generate a diagnostic report, then decide the next move based on evidence.

Here is the full corrected roadmap, including augmentation.

**Phase 0: Dataset Audit**
Before augmentation, verify the dataset.

Ask coder to report:

```text
contract-level split leakage
duplicate/near-duplicate contracts
positive/negative count by vulnerability type
interactions per contract
false label suspicion
missing fields in positive interactions
```

Decision gate:

```text
If leakage exists, rebuild split.
If labels are noisy, clean before training.
```

**Phase 1: Redirect Task Setting**
Move from strict interaction-level classification to:

```text
contract-level detection + top-k interaction localization
```

Metrics:

```text
contract precision/recall/F1
top-1/top-3/top-5 localization
MRR
interaction PR-AUC as secondary
```

This should be done before major architecture work.

**Phase 2: Train-Only Data Augmentation**
Augment only the training positives.

Safe augmentation:

```text
variable/function renaming
contract renaming
formatting/comment changes
dead code insertion
unused helper functions
unused state variables
safe declaration reordering
```

Avoid risky augmentation:

```text
changing modifiers
changing visibility
moving state updates
changing external call target
changing require conditions
```

Goal:

```text
3x-5x positive expansion
```

Report:

```text
performance before/after augmentation
per-vulnerability recall
overfitting check
embedding stability
```

**Phase 3: Loss + Calibration**
Use:

```text
class-balanced focal loss
positive oversampling
Platt/isotonic calibration
threshold tuning for recall 80/90
```

Goal:

```text
raise recall without destroying precision
```

**Phase 4: Contract-Level Aggregation**
Score interactions, then aggregate to contract prediction:

```text
max pooling
top-k pooling
attention pooling
MIL loss
```

Training objective:

```text
positive contract: at least one interaction high
negative contract: all interactions low
```

This is where the new setting starts helping.

**Phase 5: Safety Feature Extraction**
Add explicit safety/protection features:

```text
CEI order
return check
nonReentrant resolved
access control resolved
require/assert guard
callee controllability
trusted/fixed callee
safe ERC20 wrapper
delegatecall target control
try/catch
```

This is the main precision booster.

**Phase 6: Risk + Safety Architecture**
Separate the model:

```text
risk encoder = vulnerable evidence
safety encoder = protection evidence
final score = risk_score - safety_score
```

Then aggregate interaction scores to contract score.

**Phase 7: Hard-Negative Mining**
Collect high-scoring negatives and retrain.

Focus on:

```text
protected reentrancy-like cases
checked low-level calls
owner-only dangerous calls
trusted external calls
safe wrappers
external call after state update
```

Report:

```text
precision change
false-positive category reduction
recall loss if any
```

**Phase 8: Contrastive / Counterfactual Training**
Create matched pairs:

```text
vulnerable interaction vs similar protected interaction
```

Train ranking:

```text
score(vulnerable) > score(protected)
```

This teaches the exact difference between positive and hard negative.

**Phase 9: Final Calibration + Ablation**
Run 5-10 seeds.

Report:

```text
without augmentation
without safety features
without contract context
without hard-negative mining
without contrastive loss
```

This is needed for the paper.

**My Recommended Working Loop**

For each phase, tell the coder:

```text
Implement only this phase.
Run 5-seed evaluation.
Generate error analysis.
Compare against previous checkpoint.
List what improved, what got worse, and the top remaining failure categories.
Do not move to the next phase automatically.
```

Expected final target in this redirected setup:

```text
Contract precision: 70-80%
Contract recall:    85-93%
Top-3 localization: 75-85%
```

So yes, your idea is right: let the AI coder implement and report step by step. The important thing is **do not blindly stack methods**. Every phase should produce a report, and the next phase should be chosen based on the remaining error pattern.
