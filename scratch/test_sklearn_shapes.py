import numpy as np
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

labels = np.array([0, 1, 0, 1, 0, 0])
pred_1d = np.array([0, 1, 0, 0, 0, 0])
pred_2d = pred_1d.reshape(-1, 1)

probs_1d = np.array([0.1, 0.9, 0.2, 0.4, 0.1, 0.1])
probs_2d = probs_1d.reshape(-1, 1)

print("1D vs 1D:")
print("F1:", precision_recall_fscore_support(labels, pred_1d, average='binary', zero_division=0)[:3])
print("ROC:", roc_auc_score(labels, probs_1d))

try:
    print("\n1D vs 2D:")
    print("F1:", precision_recall_fscore_support(labels, pred_2d, average='binary', zero_division=0)[:3])
    print("ROC:", roc_auc_score(labels, probs_2d))
except Exception as e:
    print("Error:", e)

