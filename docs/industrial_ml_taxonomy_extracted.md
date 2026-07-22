Industrial ML Taxonomy: Regression & Anomaly Detection
Platform blueprint for industrial sensor and manufacturing data
0. Executive summary
Regression and anomaly detection (AD) are the two workhorse problem families in
industrial ML — soft sensors, RUL, yield, and quality prediction on one side; fault detection,
drift, and defect detection on the other. They look similar at the infrastructure level (same
sensors, same time-series shape, same ingestion path) but diverge sharply at the modeling
level (different objectives, different label regimes, different failure modes). A platform that
tries to force both into one modeling pipeline will break; a platform that shares nothing will
duplicate effort and drift out of sync.
Four principles drive every decision in this document:
1. Label availability is the real fork in the road, not the algorithm family. Regression
almost always needs a continuous ground truth; AD usually has to work with little or
no fault labels, which is why semi-supervised (train-on-normal) approaches dominate
industrial AD.
2. Time-series vs. tabular vs. multivariate sensor data changes validation strategy,
feature engineering, and model class — this cuts across both families, so treat it as an
orthogonal axis, not a regression-only or AD-only concern.
3. Infrastructure is shared, modeling logic is not. Ingestion, schema validation, the
feature store, the model registry, and the monitoring stack can be one shared system.
Loss functions, thresholds, and evaluation metrics cannot.
4. The scenario checklist is the actual deliverable. Algorithms come and go; the list of
real-world scenarios a platform must be able to express (RUL, soft sensor, sensor
dropout, novel operating mode, collective drift, etc.) is what prevents a costly redesign
six months in.
1. Regression hierarchy
1.1 Target types
Target type Description Example
Scalar continuousSingle numeric value, one prediction per
recordPredicted outlet temperature
Multi-output /
vectorSeveral correlated continuous targets
predicted jointlyPredicting tensile strength,
hardness, and thicknessTarget type Description Example
together
Time-to-event
(survival-like)Continuous target with censoring — asset
may still be running when data is collectedRemaining Useful Life (RUL)
Horizon forecastTarget is the sensor's own future value at t+hLoad forecast 4 hours ahead
Ordinal-
continuous
hybridContinuous internally but
reported/consumed as a bounded scoreInline quality score (0–100)
mapped to a lab grade
1.2 Input data types
Tabular process parameters (setpoints, batch recipe ﬁelds, static conﬁg)
Time-series sensor streams — single-channel or multi-channel, uniform or mixed
sample rate
Spectral / vibration data (FFT-ready waveform segments)
Vision-derived features (extracted embeddings or measurements from inline
cameras)
Static asset metadata (machine age, model, maintenance history, install date)
Event and maintenance logs (work orders, alarms, operator notes)
1.3 Common industrial scenarios
Soft sensor / virtual sensor — predicting a hard-to-measure or expensive-to-measure
variable (e.g. composition) from cheap, fast sensors.
Remaining Useful Life (RUL) estimation — predicting time-to-failure or time-to-
maintenance from degradation signals.
Quality measurement prediction — predicting a lab test result (destructive or slow)
from inline process sensors, enabling real-time release decisions.
Yield prediction — predicting batch or line yield from process conditions.
Energy / utility consumption prediction — predicting power, steam, or compressed-
air draw.
Cycle time / throughput prediction — predicting how long a batch or unit operation
will take.
Short-horizon forecasting — demand, load, or consumption forecasting, which is
regression against a shifted target.
Multi-output regression — jointly predicting several correlated quality attributes to
preserve their correlation structure, rather than training N independent models.Algorithm Best for When to use Strengths Weaknesses
Linear / Ridge
/ Lasso / PLSHigh-
dimensional
collinear sensor
data
(spectroscopy,
chemometrics)Small-to-medium
data,
interpretability
required, strong
multicollinearityFast,
interpretable,
stable with
regularizationMisses non-linear
interactions
Gradient
boosted trees
(XGBoost,
LightGBM,
CatBoost)Structured
tabular process
dataMedium-to-large
data, non-linear
interactions,
mixed feature
typesStrong default
baseline,
handles
missing values,
feature
importance
built inNeeds care with
temporal leakage,
weaker on raw
sequences
Random
ForestRobust
baseline, noisy
sensor dataQuick baseline,
noisy or small
data, need feature
importanceRobust to
outliers, low
tuning effortLess accurate than
boosting on large clean
data
Support
Vector
Regression
(SVR)Small, smooth-
function dataSmall datasets,
smooth non-
linear
relationshipsWorks well
with limited
dataScales poorly, sensitive
to
kernel/hyperparameter
choice
Gaussian
Process
RegressionSmall data
needing
uncertaintyNeed calibrated
conﬁdence
intervals, sparse
dataNative
uncertainty
estimatesComputationally
expensive beyond a few
thousand rows
MLP (feed-
forward
neural net)Tabular data
with complex
interactionsLarge tabular
datasets, non-
linear feature
interactionsFlexible, scales
with dataNeeds more data and
tuning than trees, less
interpretable
LSTM / GRUSequential
regression
where history
mattersRUL, degradation
trends, variable-
length sequencesCaptures long-
range temporal
dependencySlower to train, needs
sequence framing,
prone to overﬁtting on
short series
TCN
(temporalSequential
regression,Long sequences,
need fasterParallel
training, longLess mature tooling
than LSTM in some
stacksAlgorithm Best for When to use Strengths Weaknesses
convolutional
network)parallelizable
trainingtraining than
RNNseffective
receptive ﬁeld
Transformer /
temporal
fusionMultiple
correlated
sensors, long
sequencesLarge ﬂeets,
many correlated
channels,
attention over
time helps
interpretabilityHandles
multivariate
long
sequences,
attention aids
explainabilityData-hungry, higher
engineering cost
Survival
regression
(Cox PH,
Weibull AFT)Censored RUL
dataAsset still
operating when
data is collected
(right-censored)Properly
handles
censoring,
statistically
principledLess familiar tooling,
assumes speciﬁc hazard
structure
Physics-
informed /
hybrid modelsKnown physical
model + sparse
dataWell-understood
physics but
insufficient data
for pure MLExtrapolates
better, needs
less dataRequires domain
physics expertise to
build
1.5 Data assumptions
Sensors sampled consistently, or a deﬁned resampling/alignment strategy exists for
mixed rates.
Training data spans the full operating envelope the model will be asked to predict on
— extrapolation outside it is unreliable.
Labels (lab results, RUL ground truth) are timestamped correctly and lag-aligned with
the sensor window that produced them.
For classic tabular ML: no data leakage across time — train/validation split must
respect chronology, not random shuffling.
Missing data has a known pattern (random vs. systematic, e.g. sensor maintenance
windows) that preprocessing accounts for.
1.6 Failure modes
Temporal leakage — using future information (e.g. a rolling feature computed across
the full series) to predict the past.
Extrapolation beyond training envelope — new operating point, new product recipe,
or new asset outside the training distribution.
Target drift — the physical relationship between sensors and target shifts over time
(equipment wear, recalibration, process change) without retraining.Degenerate / stuck sensor — a frozen or ﬂat-lined sensor gets picked up as a spurious
strong predictor.
Asset-speciﬁc overﬁtting — a model trained on one machine fails to generalize
across a ﬂeet with slightly different dynamics.
Label scarcity for RUL/quality — destructive testing or slow lab cycles mean very few
true labels, forcing heavy reliance on proxy labels.
1.7 Evaluation metrics
RMSE, MAE, MAPE, R² as baseline metrics.
NRMSE (normalized RMSE) when comparing performance across assets or units
with different scales.
For RUL speciﬁcally: asymmetric scoring that penalizes late predictions more than
early ones (e.g. the PHM08-style scoring function), since predicting failure too late is
operationally worse than predicting it too early.
For multi-output regression: report per-target metrics individually, plus one aggregate
(e.g. mean NRMSE) — never collapse to a single number without the breakdown.
1.8 Preprocessing & feature engineering
Resampling and time alignment across multi-rate sensors to a common clock.
Rolling statistics: mean, std, min/max, slope over multiple window lengths.
Lag features for known-delay relationships (e.g. sensor-to-lab-result lag).
Spectral / FFT features for vibration and acoustic signals.
Domain-speciﬁc degradation indices (e.g. cumulative wear proxies) where physical
knowledge exists.
Outlier clipping or winsorizing before scaling.
Per-asset vs. global normalization — decide based on whether cross-asset
comparability or single-asset precision matters more.
Explicit handling of censored or missing labels rather than silent row-dropping.
1.9 Pipeline stages
Ingestion → time alignment/resampling → data validation → feature engineering → time-
aware train/validation split → model training → evaluation → calibration (for conﬁdence
intervals where relevant) → deployment → monitoring.2. Anomaly detection hierarchy
2.1 Types of anomalies
Type Description
Point anomaly A single observation that is anomalous relative to the rest of the data (a spike)
Contextual
anomalyNormal value in general, but abnormal given the current context (e.g. high
temperature is normal in summer, anomalous in winter for the same
setpoint)
Collective /
sequence anomalyIndividual points look normal, but the pattern over a window is abnormal (a
slow oscillation, a subtle regime change)
Drift-related
anomalyThe data-generating process itself shifts over time (concept drift), which can
either be the anomaly of interest or a source of false alarms if not modeled
separately
2.2 Supervision levels
Supervised — labeled fault and normal examples exist; framed as classiﬁcation. Rare
in industrial settings because faults are infrequent and expensive to label.
Semi-supervised (train-on-normal) — the dominant industrial pattern. Model learns
what "normal" looks like from a clean training set, then ﬂags deviations. Doesn't
require fault labels, only a curated normal period.
Unsupervised — no labels of any kind; relies purely on statistical or structural
properties of the data (density, distance, clustering) to ﬂag rare points.
2.3 Input data types
Same categories as regression (tabular, time-series, spectral, vision, static metadata) — the
same sensor infrastructure feeds both problem families.
2.4 Common industrial scenarios
Equipment fault detection — bearing wear, pump cavitation, motor imbalance.
Sensor spike and dropout detection — data-quality anomalies that must be
distinguished from process anomalies.
Novelty detection — ﬂagging a genuinely new operating mode the model has never
seen (new product, new recipe, new ambient condition).
Process deviation detection — the process drifts outside its normal operating band
without a discrete fault event.
Predictive maintenance early warning — subtle multivariate deviation that precedes
a known failure mode by hours or days.Visual / quality defect detection — anomalies in vision-derived features (surface
defects, misalignment).
OT / cybersecurity anomaly — anomalous command or network patterns on
operational technology; same statistical toolkit, different feature space and much
higher false-positive cost tolerance for security triage.
2.5 Algorithm guide by category
Method Anomaly
type ﬁtWhen to use Strengths Weaknesses
Rule / threshold-
based (SPC
charts: Shewhart,
CUSUM, EWMA)Point, driftDomain SME
thresholds are
known,
interpretability is
critical,
regulatory audit
trail neededFully
interpretable,
easy to explain
to operatorsMisses multivariate and
contextual anomalies,
brittle to legitimate
regime changes
Statistical /
density (Z-score,
Mahalanobis
distance,
Hotelling's T²,
GMM, KDE)Point,
contextualLinear
correlation
structure among
sensors is known
and stableStatistically
grounded, fast to
computeAssumes a distribution
shape, weak with strong
non-linearity
Distance /
cluster-based (k-
NN distance, k-
means distance,
DBSCAN)Point,
noveltyFast
unsupervised
baseline,
moderate
dimensionalityNo
distributional
assumption,
simple to
implementStruggles in high
dimensions, sensitive to
distance metric choice
Isolation ForestPoint,
noveltyFast
unsupervised
baseline across
many featuresScales well, no
distance
computation,
handles high
dimensionalityLess effective on
strongly
sequential/contextual
anomalies
One-Class SVM /
SVDDPoint,
noveltySmall clean
training set, tight
normal
boundary
neededWorks with
limited normal
dataSensitive to
kernel/hyperparameter
tuning, scales poorlyMethod Anomaly
type ﬁtWhen to use Strengths Weaknesses
Reconstruction-
based (PCA
residual,
Autoencoder,
VAE, LSTM-
Autoencoder)Point,
contextual,
collectiveNon-linear
multivariate
relationships,
sequential dataCaptures
complex
multivariate
structure,
LSTM-AE
captures
temporal
patternNeeds enough clean
normal data to learn
reconstruction well, can
be opaque
Forecasting-
residual based
(predict next
value, ﬂag large
residual)Point,
contextualBridges
regression and
AD — useful
when a good
forecasting
model already
existsReuses
regression
infrastructure,
intuitiveResidual threshold
needs careful calibration,
sensitive to forecast
model drift
Supervised
classiﬁers (RF,
GBM, NN)Point,
collectiveEnough labeled
fault examples
exist and fault
modes are stableHighest
precision when
labels are
availableRequires labeled faults,
which are rare and
expensive
Changepoint
detection
(CUSUM,
Bayesian online
changepoint)Drift Monitoring for a
regime shift
rather than a
point outlierDetects gradual
shifts other
methods missDetection delay is
inherent to the method,
needs tuning of
sensitivity
Matrix proﬁle /
discordsCollective /
sequenceLong time-series
where the shape
of a subsequence
matters more
than any single
valueFinds subtle
repeating-
pattern
anomalies
without labelsComputationally heavier
on very long series
2.6 Data assumptions
The "normal" training period genuinely represents typical operation across all valid
regimes (shifts, seasons, product types) — not just one slice of it.
For semi-supervised methods: the normal training set is contamination-free (no
undetected faults baked into "normal").
Enough history exists to characterize normal variability, including legitimate regime
changes, so they aren't ﬂagged as anomalies.2.7 Failure modes
Contaminated normal set — undetected faults inside what was assumed to be clean
training data quietly raise the threshold.
Multiple valid operating modes not modeled — a legitimate regime change gets
ﬂagged as an anomaly (a major source of alarm fatigue).
Sensor drift mistaken for process anomaly — gradual sensor calibration drift looks
identical to a genuine slow-developing fault.
Alarm fatigue — threshold set too sensitive, operators start ignoring alerts.
Silent model staleness — the normal envelope shifts (new product mix, seasonal
change) but the model isn't retrained, causing both missed detections and false
alarms.
Boundary too tight or too loose — one-class boundary methods (SVM/SVDD,
Isolation Forest) need re-validation whenever the operating envelope changes.
2.8 Evaluation metrics
Precision, recall, F1 — with explicit attention to class imbalance (anomalies are rare by
deﬁnition).
ROC-AUC and PR-AUC (PR-AUC is usually more informative given the imbalance).
Detection latency / time-to-detect — often more important operationally than point-
level precision.
False alarm rate per week — the business-facing metric that determines whether
operators trust the system.
Point-adjust evaluation caveats — a common evaluation trick (crediting a whole
anomalous segment as detected if any point in it was ﬂagged) can inﬂate reported
performance; state clearly which convention is used.
For changepoint detection speciﬁcally: detection delay from the true changepoint.
2.9 Preprocessing & feature engineering
Same alignment/resampling pipeline as regression.
Residual features (from a forecasting or reconstruction model) as anomaly-scoring
inputs.
Rolling z-scores and rolling statistics for contextual anomaly detection.
Wavelet / FFT features for vibration-based fault detection.
Dimensionality reduction (PCA) before reconstruction-based modeling to control the
effective feature space.
Per-operating-mode normalization — normalize within each known regime rather
than globally, when multiple valid modes exist.
Careful label curation for the supervised branch — fault tagging protocol should be
documented and consistent.2.10 Pipeline stages
Ingestion → data validation → normal-state feature engineering → model training (on
curated normal data for semi-supervised methods) → threshold calibration (e.g. based on a
validation-set percentile) → evaluation → alerting/monitoring integration → retraining
trigger via drift detection on the input feature distribution.
3. Shared pipeline architecture
3.1 End-to-end structure
Ingestion → schema validation → time alignment/resampling → data quality checks →
feature engineering (shared library) → [regression training / evaluation] or [AD training /
threshold calibration] → deployment (shared serving layer) → monitoring and drift
tracking (shared) → retraining trigger.
(See the diagram above for the visual layout of this ﬂow.)
3.2 Stages that can be shared
Data ingestion and connector layer.
Schema validation and data-quality checks.
Time alignment / resampling utilities.
The feature engineering library (rolling stats, lag features, spectral features, cross-
sensor ratios) — same transforms, reused by both families.
Experiment tracking (run metadata, parameters, artifacts).
Model registry and versioning.
Deployment / serving infrastructure.
Monitoring infrastructure (metric collection, dashboards, alerting transport).
The general retraining orchestration skeleton (the scheduler and trigger mechanism,
not the retraining logic itself).
3.3 What goes into each stage
Data validation: schema conformance, per-sensor range checks, missing-value rate
thresholds, timestamp continuity/gap detection, duplicate-record detection, unit and
sensor-identity consistency, cross-sensor correlation sanity checks (catches
wiring/tagging errors).
Feature engineering: the shared transform library described above, parameterized
per use case rather than duplicated per model.
Model training: shared training harness (data loaders, experiment logging) wrapping
a family-speciﬁc objective — continuous loss for regression,
reconstruction/density/margin objective for AD.Evaluation: family-speciﬁc metric modules (Section 1.7 and 2.8) computed through a
shared evaluation harness so results land in the same tracking system.
Explainability: SHAP or feature-importance tooling shared at the library level, but
the interpretation differs — for regression it explains what drives the predicted value,
for AD it explains what drives the deviation from normal.
Monitoring and drift tracking: shared drift detection on input feature distributions
(e.g. population stability index, KS-test), but the downstream action differs — for
regression, performance decay triggers a retrain; for AD, drift can mean either
"recalibrate the threshold" or "retrain the normal-state model," and the platform must
distinguish which.
4. Separate pipeline requirements
These must not be uniﬁed, even though the surrounding infrastructure is shared:
Label handling — regression needs a continuous ground-truth value; AD needs either
a curated "normal period" deﬁnition (semi-supervised) or fault labels (supervised).
These are structurally different data contracts, not variations of the same one.
Training objective / loss function — continuous regression loss vs. reconstruction
loss, density estimation, or margin-based objectives.
Threshold calibration — unique to AD; regression has no equivalent concept.
Evaluation metric computation — RMSE-family metrics vs.
precision/recall/detection-latency metrics measure fundamentally different things.
Alerting and downstream action logic — a regression prediction feeds a dashboard
or a control loop; an AD ﬂag feeds an alarm/ticketing workﬂow with its own escalation
rules.
Retraining trigger semantics — "performance decayed, retrain" (regression) vs.
"input distribution drifted, recalibrate threshold or retrain the normal model" (AD)
are different decisions requiring different signals.
5. Industrial considerations
Schema differences. Sensor naming, units, and tag structures vary by plant, line, and even
by shift-to-shift conﬁguration changes. A multi-tenant platform needs a canonical schema
mapping layer (per-tenant tag registry) between raw ingestion and the shared feature
engineering library — without it, every new site becomes a bespoke integration project
instead of a conﬁguration exercise.
Time-series vs. tabular vs. multivariate. Time-series data forces a chronological
train/validation split (never random shuffling) and favors sequence-aware models
(LSTM/TCN/Transformer) or careful windowed feature engineering. Tabular data (e.g. per-
batch summary records) tolerates standard cross-validation. Multivariate sensor arraysneed correlation-aware feature engineering and often beneﬁt from dimensionality
reduction before modeling, especially for reconstruction-based AD.
Label availability. This is the single biggest driver of algorithm choice. Abundant labels →
supervised regression and supervised AD classiﬁers become viable. Scarce labels (the
industrial default, since lab tests and fault tagging are slow and expensive) → soft-sensor
regression with proxy labels, and semi-supervised (train-on-normal) AD.
Uniﬁed vs. separate framework decision. The right pattern is "one platform, many
pipelines": unify the infrastructure layer (ingestion, validation, feature store, deployment,
monitoring) and keep the modeling layer (objective, threshold, evaluation, alerting)
separate per family. Attempting a single uniﬁed modeling pipeline for both families is the
most common design mistake in industrial ML platforms.
What must not be forced into a shared pipeline: loss functions, threshold logic, label
schemas, evaluation metric modules, alerting/escalation logic.
What is safe to generalize: ingestion, schema validation, the feature transform library, the
model registry, deployment/serving, and the monitoring/drift-detection infrastructure
(with family-speciﬁc action logic layered on top).
6. Decision table for algorithm selection
Scenario Data type Label
availabilityRecommended
approachFallback
Soft sensor / virtual
sensorMultivariate
time-seriesContinuous
labels
available
(lagged)Gradient boosted
trees or LSTM if
strong temporal
dependencyLinear/PLS if
highly collinear
and small data
RUL estimation Time-series,
degradation
trendCensored
continuous
(asset may
still be
running)Survival
regression
(Cox/Weibull) or
LSTM with
asymmetric
scoringGBM on hand-
engineered
degradation
features
Quality prediction
from inline sensorsTabular +
time-seriesSparse lab
labelsGBM with careful
lag alignmentPLS regression
(chemometrics-
style)
Yield prediction Tabular (batch
records)Continuous,
moderate
volumeGBM or Random
ForestLinear regression
baselineScenario Data type Label
availabilityRecommended
approachFallback
Energy consumption
predictionTime-seriesContinuous,
abundantGBM or TCN Linear regression
with rolling
features
Equipment fault
detection, known
fault modesTime-series /
vibrationSome labeled
faultsSupervised
classiﬁer
(RF/GBM)Semi-supervised
reconstruction
model if labels too
few
Equipment fault
detection,
unknown/rare faultsTime-series /
vibrationNo fault labelsSemi-supervised
Autoencoder or
Isolation ForestPCA residual +
threshold
Sensor spike/dropout
detectionTime-series,
single or few
channelsUsually noneRule/threshold-
based (SPC)Z-score / rolling
statistics
Novelty detection
(new operating
mode)Multivariate
tabular/time-
seriesNone One-Class SVM or
Isolation ForestDistance-based
(k-NN)
Process deviation /
drift monitoringMultivariate
time-seriesNone Changepoint
detection
(CUSUM)PSI/KS-test on
features
Predictive
maintenance early
warningMultivariate
time-seriesLittle to noneLSTM-
Autoencoder or
forecasting-
residual methodPCA
reconstruction
error
Visual/quality defect
detectionImage-
derived
featuresSome labeled
defectsSupervised
classiﬁer on
embeddingsOne-class model
on "good"
embeddings only
Collective/sequence
pattern anomalyLong time-
seriesNone Matrix proﬁle /
discordsLSTM-
Autoencoder
7. Checklist of scenarios that must not be missed
Regression
 Soft sensor / virtual sensor prediction
 RUL estimation with censored data handling Quality prediction with sparse, lagged lab labels
 Yield prediction
 Energy/utility consumption prediction
 Cycle time / throughput prediction
 Short-horizon forecasting framed as regression
 Multi-output regression preserving cross-target correlation
 Per-asset vs. ﬂeet-wide generalization
Anomaly detection
 Point anomaly detection (spikes)
 Contextual anomaly detection (context-dependent thresholds)
 Collective / sequence anomaly detection (subtle pattern shifts)
 Drift-related anomaly / changepoint detection
 Equipment fault detection with and without labels
 Sensor spike and dropout detection (data-quality vs. process anomaly)
 Novelty detection for new operating modes
 Cluster-based anomaly detection
 Reconstruction-based anomaly detection (PCA, Autoencoder, LSTM-AE)
 Density-based anomaly detection
 Rule/threshold-based detection with SME-deﬁned limits
 Multiple legitimate operating regimes explicitly modeled (not ﬂagged as anomalies)
Platform-level
 Canonical schema mapping for multi-tenant/multi-site onboarding
 Chronological (not random) train/validation splitting wherever time-series data is
involved
 Separate label contracts for regression vs. AD
 Separate threshold-calibration logic isolated from the shared training harness
 Drift monitoring wired to two distinct actions (retrain vs. recalibrate) depending on
family
 Explainability tooling adapted per family, not assumed identical