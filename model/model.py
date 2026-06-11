import torch
import torch.nn as nn

class AttentionPooling(nn.Module):
    """
    Computes learned attention weights over hyperedge member nodes and
    pools them into a single hyperedge vector.
    """
    def __init__(self, input_dim=768, hidden_dim=128):
        super().__init__()
        self.w_a = nn.Linear(input_dim, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)
        
    def forward(self, x, mask=None):
        # x shape: (B, N, input_dim)
        # mask shape: (B, N) where True/1 indicates active nodes, False/0 represents padding
        scores = self.v(torch.tanh(self.w_a(x)))  # (B, N, 1)
        scores = scores.squeeze(-1)  # (B, N)
        
        if mask is not None:
            # Mask out padded positions using negative infinity to make softmax 0
            scores = scores.masked_fill(~mask, -1e9)
            
        attn_weights = torch.softmax(scores, dim=-1)  # (B, N)
        attn_weights_unsqueezed = attn_weights.unsqueeze(-1)  # (B, N, 1)
        
        pooled = torch.sum(attn_weights_unsqueezed * x, dim=1)  # (B, input_dim)
        return pooled, attn_weights

class HyperedgeClassifier(nn.Module):
    """
    A simple classifier that pools node embeddings and feeds the pooled
    hyperedge embedding into a 2-layer MLP head.
    """
    def __init__(self, input_dim=768, hidden_dim=256, dropout=0.3):
        super().__init__()
        self.pool = AttentionPooling(input_dim=input_dim, hidden_dim=128)
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1)
        )
        
    def forward(self, x, mask=None):
        pooled, attn_weights = self.pool(x, mask)
        logits = self.mlp(pooled)  # (B, 1)
        return logits, attn_weights
