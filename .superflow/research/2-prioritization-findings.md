# Keyword Prioritization - Key Findings

## Industry-Standard Formula Pattern

```
Opportunity Score = (Volume × W1) + (Intent × W2) + (Position × W3) 
                    - (Difficulty × W4) + (Additional × W5)
```

## Recommended Weights (Medical Marketing)

```python
weights = {
    'volume': 0.20,      # 20% - traffic potential
    'intent': 0.30,      # 30% - conversion likelihood (HIGH for medical)
    'difficulty': 0.25,  # 25% - ranking feasibility
    'position': 0.15,    # 15% - quick win potential
    'trend': 0.10        # 10% - future value
}
```

## Normalization Techniques

### Volume: Log Scale
```python
volume_norm = min(100, (LOG10(volume) / LOG10(100000)) * 100)
```
**Why:** Prevents high-volume keywords from dominating

### Difficulty: Inverted + Exponential Penalty
```python
difficulty_norm = 100 - difficulty
difficulty_gate = (1 - (difficulty/100)²)
```
**Why:** KD 70+ requires disproportionate effort

### Intent: 1-5 Scale with Multipliers
```python
intent_multipliers = {
    'transactional': 1.2,    # comparison/buying
    'commercial': 1.0,       # tool selection
    'educational': 0.8       # awareness
}
```

## Priority Thresholds (P0-P3)

| Priority | Score | Criteria | Action |
|----------|-------|----------|--------|
| P0 | 80-100 | High volume + low difficulty + high intent | Create immediately |
| P1 | 65-79 | Strong balance, quick wins (pos 11-20) | Queue for next sprint |
| P2 | 45-64 | Moderate opportunity, medium-term | Plan for future |
| P3 | 25-44 | Monitor only | Track but don't prioritize |

## SERP Feature Penalties

```python
serp_penalties = {
    'featured_snippet': 0.4,
    'ai_overview': 0.5,      # AI Overviews steal 50% clicks
    'local_pack': 0.5,
    'knowledge_panel': 0.3,
}
```

## Production-Ready Formula

```python
def calculate_keyword_priority(
    volume: int,
    difficulty: int,
    intent_score: int,  # 1-5
    current_position: int,
    serp_features: list,
    trend_direction: str
) -> dict:
    # Normalize (0-100)
    vol_norm = min(100, (math.log10(volume) / math.log10(100000)) * 100)
    diff_norm = 100 - difficulty
    intent_norm = (intent_score / 5) * 100
    pos_norm = max(0, 100 - (current_position * 3))
    trend_norm = {'rising': 100, 'stable': 70, 'declining': 40}[trend_direction]
    
    # Weighted score
    base_score = (
        vol_norm * 0.20 +
        intent_norm * 0.30 +
        diff_norm * 0.25 +
        pos_norm * 0.15 +
        trend_norm * 0.10
    )
    
    # SERP penalty
    total_penalty = sum(serp_penalties.get(f, 0) for f in serp_features)
    final_score = base_score * (1 - min(0.8, total_penalty))
    
    # Classify
    if final_score >= 80: priority = "P0"
    elif final_score >= 65: priority = "P1"
    elif final_score >= 45: priority = "P2"
    elif final_score >= 25: priority = "P3"
    else: priority = "SKIP"
    
    return {'score': round(final_score, 1), 'priority': priority}
```

## Key Insights

1. ✅ Multi-factor beats single-metric (volume alone misleading)
2. ✅ Log normalization prevents volume dominance
3. ✅ Difficulty penalties are exponential (KD 70+ = disproportionate effort)
4. ✅ SERP features reduce opportunity (AI Overviews steal 40-50% clicks)
5. ✅ Intent weighs heavily (transactional = 1.2-1.5× informational)
