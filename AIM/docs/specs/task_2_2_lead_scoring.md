"""AI Lead Scoring Specification

Task: Phase 11 Sprint 2 - Task 2.2
Duration: 16 hours
Status: Planning

## Overview

AI-powered lead scoring system that evaluates lead quality using 30+ factors
and assigns priority tiers (Hot/Warm/Cold) for sales team follow-up.

## Goals

1. **Automatic Lead Qualification**: Score leads 0-100 based on conversion probability
2. **Priority Tiering**: Classify leads as Hot (80-100), Warm (50-79), Cold (0-49)
3. **Real-time Scoring**: Score leads immediately after capture (<1 second)
4. **Explainable AI**: Provide reasoning for scores (top 5 factors)
5. **Continuous Learning**: Update model based on conversion outcomes

## Architecture

```
Lead Captured
    ↓
LeadScoringService
    ↓
Feature Extraction (30+ factors)
    ↓
ML Model (XGBoost/LightGBM)
    ↓
Score (0-100) + Tier (Hot/Warm/Cold) + Explanation
    ↓
Update Lead Record
    ↓
Trigger Follow-up Workflow
```

## Scoring Factors (30+)

### 1. Demographic Factors (10 points)
- **Specialty match** (5 points): High-value specialties (dentistry, plastic surgery)
- **Clinic size** (3 points): Inferred from clinic name (chain vs single)
- **Location** (2 points): Major cities (Moscow, St. Petersburg) vs regions

### 2. Behavioral Factors (20 points)
- **Message quality** (10 points): Detailed inquiry vs generic
- **Response time** (5 points): Business hours vs off-hours
- **UTM campaign** (5 points): High-intent campaigns (implants, surgery)

### 3. Engagement Factors (15 points)
- **Form completion** (5 points): All fields filled vs minimal
- **Message length** (5 points): >50 words = high intent
- **Contact method** (5 points): Phone + email vs email only

### 4. Technical Factors (10 points)
- **Device type** (3 points): Desktop (higher intent) vs mobile
- **Browser** (2 points): Chrome/Safari (professional) vs others
- **Session duration** (5 points): >2 minutes on site = high intent

### 5. Timing Factors (10 points)
- **Day of week** (5 points): Weekdays (higher intent) vs weekends
- **Time of day** (5 points): Business hours (9-18) vs off-hours

### 6. Source Factors (15 points)
- **Traffic source** (10 points): Organic search (high intent) vs paid ads
- **Referral** (5 points): Direct referral (highest intent) vs cold traffic

### 7. Historical Factors (10 points)
- **Previous submissions** (5 points): First-time vs repeat (lower score)
- **Email domain** (5 points): Business domain vs free email (gmail, yandex)

### 8. Compliance Factors (10 points)
- **ФЗ-152 consent** (5 points): Explicit consent (required)
- **Data completeness** (5 points): All required fields filled

## ML Model

### Model Choice: XGBoost

**Why XGBoost:**
- Fast inference (<10ms)
- Handles missing values
- Feature importance (explainability)
- Works well with small datasets (100+ leads)
- No need for feature scaling

**Alternative: LightGBM** (if XGBoost too slow)

### Training Data

**Minimum:** 100 leads with conversion outcomes
**Optimal:** 1,000+ leads

**Features (30+):**
- Specialty (categorical)
- Message length (numeric)
- Response time (numeric)
- UTM parameters (categorical)
- Device type (categorical)
- Day of week (categorical)
- Time of day (numeric)
- Source (categorical)
- Email domain type (categorical)
- Form completion rate (numeric)
- Session duration (numeric)
- Previous submissions (numeric)

**Target:** Conversion (0/1) - Did lead convert to client?

### Model Training

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split

# Load training data
X_train, X_test, y_train, y_test = train_test_split(
    features, conversions, test_size=0.2, random_state=42
)

# Train XGBoost
model = xgb.XGBClassifier(
    max_depth=5,
    learning_rate=0.1,
    n_estimators=100,
    objective="binary:logistic",
    eval_metric="auc",
)
model.fit(X_train, y_train)

# Evaluate
score = model.score(X_test, y_test)
print(f"Accuracy: {score:.2%}")

# Feature importance
importance = model.feature_importances_
```

### Model Serving

**Option 1: In-memory (Recommended for MVP)**
- Load model at service startup
- Predict in-process (<10ms)
- No external dependencies

**Option 2: Model server (Future)**
- TensorFlow Serving / TorchServe
- Separate model service
- Versioning and A/B testing

## Implementation

### 1. Feature Extractor

```python
class LeadFeatureExtractor:
    """Extract 30+ features from lead data"""
    
    def extract(self, lead: Lead, metadata: dict) -> dict[str, Any]:
        """Extract features for scoring
        
        Args:
            lead: Lead record
            metadata: Request metadata (user_agent, utm, etc.)
            
        Returns:
            Dictionary of features
        """
        return {
            # Demographic
            "specialty": lead.specialty,
            "clinic_size": self._infer_clinic_size(lead.clinic_name),
            "location": self._infer_location(lead.phone),
            
            # Behavioral
            "message_quality": self._score_message(lead.message),
            "response_time": self._get_response_time(lead.created_at),
            "utm_campaign": metadata.get("utm_campaign"),
            
            # Engagement
            "form_completion": self._calc_completion_rate(lead),
            "message_length": len(lead.message or ""),
            "has_phone_and_email": True,
            
            # Technical
            "device_type": self._parse_device(metadata.get("user_agent")),
            "browser": self._parse_browser(metadata.get("user_agent")),
            "session_duration": metadata.get("session_duration", 0),
            
            # Timing
            "day_of_week": lead.created_at.weekday(),
            "hour_of_day": lead.created_at.hour,
            
            # Source
            "traffic_source": lead.source,
            "is_referral": lead.source == "referral",
            
            # Historical
            "previous_submissions": self._count_previous(lead.email_hash),
            "email_domain_type": self._classify_email_domain(lead.email),
            
            # Compliance
            "fz152_consent": lead.fz152_consent,
            "data_completeness": self._calc_completeness(lead),
        }
```

### 2. Lead Scoring Service

```python
class LeadScoringService:
    """AI-powered lead scoring service"""
    
    def __init__(self, model_path: str):
        self.model = xgb.Booster()
        self.model.load_model(model_path)
        self.feature_extractor = LeadFeatureExtractor()
    
    async def score_lead(
        self,
        lead: Lead,
        metadata: dict,
    ) -> LeadScore:
        """Score lead and assign tier
        
        Args:
            lead: Lead record
            metadata: Request metadata
            
        Returns:
            LeadScore with score, tier, explanation
        """
        # Extract features
        features = self.feature_extractor.extract(lead, metadata)
        
        # Predict score (0-100)
        X = self._features_to_array(features)
        probability = self.model.predict(xgb.DMatrix(X))[0]
        score = int(probability * 100)
        
        # Assign tier
        tier = self._assign_tier(score)
        
        # Get explanation (top 5 factors)
        explanation = self._explain_score(features, score)
        
        return LeadScore(
            score=score,
            tier=tier,
            explanation=explanation,
            factors=features,
        )
    
    def _assign_tier(self, score: int) -> str:
        """Assign tier based on score"""
        if score >= 80:
            return "Hot"
        elif score >= 50:
            return "Warm"
        else:
            return "Cold"
    
    def _explain_score(
        self,
        features: dict,
        score: int,
    ) -> list[str]:
        """Generate explanation for score
        
        Returns top 5 factors that influenced score
        """
        # Get feature importance from model
        importance = self.model.get_score(importance_type="gain")
        
        # Sort by importance
        sorted_features = sorted(
            importance.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        
        # Generate human-readable explanations
        explanations = []
        for feature, value in sorted_features:
            explanation = self._feature_to_text(feature, features[feature])
            explanations.append(explanation)
        
        return explanations
```

### 3. Schemas

```python
class LeadScore(BaseModel):
    """Lead scoring result"""
    
    score: int = Field(..., ge=0, le=100, description="Lead score (0-100)")
    tier: str = Field(..., description="Lead tier (Hot/Warm/Cold)")
    explanation: list[str] = Field(..., description="Top 5 factors")
    factors: dict[str, Any] = Field(..., description="All extracted features")
    scored_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "score": 85,
                "tier": "Hot",
                "explanation": [
                    "High-value specialty: Plastic Surgery (+15 points)",
                    "Detailed inquiry message (+12 points)",
                    "Business hours submission (+8 points)",
                    "Organic search traffic (+10 points)",
                    "First-time submission (+5 points)",
                ],
                "factors": {
                    "specialty": "plastic_surgery",
                    "message_length": 150,
                    "hour_of_day": 14,
                    "traffic_source": "organic_search",
                    "previous_submissions": 0,
                },
                "scored_at": "2026-05-16T20:30:00Z",
            }
        }
```

## Integration with Lead Capture

Update `lead_capture.py`:

```python
async def _process_lead_async(self, lead_id: str) -> None:
    """Process lead asynchronously (scoring, Linear, email)"""
    try:
        # 1. Load lead
        lead = await self._load_lead(lead_id)
        
        # 2. Score lead (NEW)
        scoring_service = LeadScoringService(model_path="models/lead_scoring.xgb")
        score_result = await scoring_service.score_lead(
            lead=lead,
            metadata={
                "user_agent": lead.user_agent,
                "utm_campaign": lead.utm_campaign,
                "session_duration": 120,  # TODO: Track from frontend
            },
        )
        
        # 3. Update lead with score
        lead.score = score_result.score
        lead.tier = score_result.tier
        await self.db.commit()
        
        # 4. Create Linear task (Task 2.3)
        # 5. Send email automation (Task 2.4)
        
    except Exception as e:
        print(f"[ERROR] Lead processing failed for {lead_id}: {e}")
```

## Testing Strategy

### 1. Unit Tests

```python
# test_feature_extractor.py
def test_extract_demographic_features():
    """Should extract specialty, clinic size, location"""
    
def test_extract_behavioral_features():
    """Should extract message quality, response time, utm"""
    
def test_extract_engagement_features():
    """Should extract form completion, message length"""

# test_lead_scoring_service.py
def test_score_lead_hot():
    """Should score high-quality lead as Hot (80-100)"""
    
def test_score_lead_warm():
    """Should score medium-quality lead as Warm (50-79)"""
    
def test_score_lead_cold():
    """Should score low-quality lead as Cold (0-49)"""
    
def test_explain_score():
    """Should return top 5 factors with explanations"""
```

### 2. Integration Tests

```python
# test_lead_scoring_integration.py
async def test_score_lead_end_to_end():
    """Should score lead and update database"""
    
async def test_scoring_performance():
    """Should score lead in <100ms"""
```

### 3. Model Tests

```python
# test_model_accuracy.py
def test_model_accuracy():
    """Should achieve >75% accuracy on test set"""
    
def test_model_feature_importance():
    """Should identify top 10 most important features"""
```

## Deployment

### 1. Model Training

```bash
# Train model on historical data
python scripts/train_lead_scoring_model.py \
    --data data/leads_with_conversions.csv \
    --output models/lead_scoring.xgb
```

### 2. Model Serving

```python
# Load model at service startup
scoring_service = LeadScoringService(
    model_path="models/lead_scoring.xgb"
)
```

### 3. Model Updates

**Frequency:** Weekly (or when 100+ new conversions)

**Process:**
1. Export leads with conversion outcomes
2. Retrain model with new data
3. Evaluate on holdout set (>75% accuracy)
4. Deploy new model (hot reload)
5. Monitor performance (A/B test if needed)

## Metrics

**Scoring Performance:**
- Inference time: <100ms per lead
- Throughput: >100 leads/second
- Model size: <10 MB

**Model Performance:**
- Accuracy: >75% on test set
- Precision (Hot tier): >80%
- Recall (Hot tier): >70%
- AUC-ROC: >0.85

**Business Metrics:**
- Hot lead conversion rate: >30%
- Warm lead conversion rate: >15%
- Cold lead conversion rate: <5%
- Sales team satisfaction: >4/5

## Russian Market Adaptations

**Specialty Weights:**
- Dentistry: High value (common, high conversion)
- Plastic Surgery: Very high value (expensive, high margin)
- Cosmetology: Medium value (competitive market)
- Ophthalmology: High value (LASIK, cataract)

**Location Weights:**
- Moscow: +10 points (highest purchasing power)
- St. Petersburg: +8 points
- Regional capitals: +5 points
- Small cities: +2 points

**Email Domain Classification:**
- Business domains (.ru, .com): +5 points
- Free email (gmail.com, yandex.ru, mail.ru): 0 points
- Suspicious domains: -5 points

## Dependencies

```
xgboost>=2.0.0          # ML model
scikit-learn>=1.3.0     # Model evaluation
pandas>=2.0.0           # Data manipulation
numpy>=1.24.0           # Numerical operations
```

## Files to Create

1. `AIM/src/aim/ai/lead_scoring/__init__.py`
2. `AIM/src/aim/ai/lead_scoring/feature_extractor.py` (300 lines)
3. `AIM/src/aim/ai/lead_scoring/scoring_service.py` (250 lines)
4. `AIM/src/aim/ai/lead_scoring/schemas.py` (100 lines)
5. `AIM/src/aim/ai/lead_scoring/model_trainer.py` (200 lines)
6. `AIM/tests/ai/lead_scoring/test_feature_extractor.py` (250 lines)
7. `AIM/tests/ai/lead_scoring/test_scoring_service.py` (200 lines)
8. `AIM/tests/ai/lead_scoring/test_integration.py` (150 lines)
9. `scripts/train_lead_scoring_model.py` (150 lines)

**Total:** 9 files, ~1,600 lines

## Timeline

**Hour 1-2:** Feature extractor implementation
**Hour 3-4:** Scoring service implementation
**Hour 5-6:** Model trainer implementation
**Hour 7-8:** Schemas and integration
**Hour 9-12:** Unit tests (feature extractor, scoring service)
**Hour 13-14:** Integration tests
**Hour 15-16:** Model training and evaluation

## Success Criteria

✅ Lead scoring service implemented
✅ 30+ features extracted
✅ XGBoost model trained (>75% accuracy)
✅ Inference time <100ms
✅ Tier assignment (Hot/Warm/Cold)
✅ Explainable AI (top 5 factors)
✅ Integration with lead capture
✅ 20+ unit tests passing
✅ 5+ integration tests passing

## Next Steps

After Task 2.2:
- Task 2.3: Linear Integration (12h) - Create tasks for Hot leads
- Task 2.4: Email Automation (10h) - Send follow-up emails by tier
- Task 2.5: Analytics Dashboard (10h) - Visualize lead scoring metrics
"""