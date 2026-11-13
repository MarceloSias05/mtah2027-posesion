# <TEAM NAME> · More than a Hack 2027 · Initial Challenge

**Frame-level ball possession for FC Barcelona vs Athletic Club**

Team: <member 1>, <member 2>, <member 3>, <member 4>, <member 5>
Repository: <public repo URL>
Submission file: `<team_name>.csv` (regenerate with `bash reproducir.sh <team_name>`)

---

## 1. Approach in one paragraph

We treat possession as a segmentation problem, not a per-frame classification problem, because that is what spellF1 rewards. A gradient-boosted classifier gives a probability of H / A / D for every frame from tracking-derived signals. A Viterbi decoder then picks the most plausible sequence of possessions over the whole match, charging a cost for every change of owner and every entry into or exit from dead ball. Since we could not tune anything on the provided game, we built a validation bench from Metrica's three public sample games and the official scorer, and every number in the pipeline was chosen there with leave-one-game-out cross-validation.

## 2. Why this approach

**What the metric rewards.** spellF1 matches whole possessions one-to-one against the truth. Splitting a long possession into three because an opponent passed near the ball for a few frames costs two false positives and usually loses the true one too. The official baseline shows this: per frame it is decent (macroF1 0.65), but unsmoothed it reports thousands of possessions and scores 0.05. Our design goal was therefore *few changes, placed at the right frame*.

**Why a bench.** The clarified rules forbid training, fitting or calibrating on the provided ground truth or video, and there is no leaderboard. Without an external place to measure, any design choice would be a guess. Metrica's public sample data (github.com/metrica-sports/sample-data, commit `e706dd5`) has three matches with tracking and synchronised event data. Game 3 is in the same EPTS format as the challenge.

From the events we derive a possession label per frame in the challenge format: the team of the last pass / carry / recovery / set piece / shot / ball lost / ball out owns the ball, and the ball is dead from a ball-out, foul or goal until the next set piece. We score with the challenge's own `evaluation/possession_metrics.py`.

To check that the bench behaves like the challenge, we ran the official baseline on it with its four smoothing windows. The ranking of the variants is the same as on BAR-ATH (window 50 best, window 125 worse, raw far worse), which gave us confidence that improvements on the bench should transfer:

| baseline window | Metrica G1 | G2 | G3 | BAR-ATH (official) |
|---|---|---|---|---|
| 0 | 0.102 | 0.087 | 0.084 | 0.049 |
| 25 | 0.347 | 0.332 | 0.318 | 0.200 |
| **50** | **0.402** | **0.390** | **0.357** | **0.243** |
| 125 | 0.283 | 0.269 | 0.296 | 0.224 |

## 3. Pipeline

**Step 1: hysteresis rule** (`src/histeresis.py`). A player "controls" the ball only if they are within *r* metres of it. The owner changes only when the other team controls the ball for *k* consecutive frames. If the ball is missing from the tracking for more than *dgap* frames, the ball is dead. Selected on the bench: r = 1.0 m, k = 8 frames (0.32 s), dgap = 25 frames (1 s). On its own this scores 0.589 out of sample (baseline 0.383).

**Step 2: per-frame classifier** (`src/segmentos.py`). Features, all of which exist identically in Metrica data and in BAR-ATH:
- ball missing flag and the length of the gap the frame sits in
- distance from the ball to the nearest home and nearest away player, and their difference
- ball speed, ball outside the pitch lines, mean player speed (1 s median)
- rolling means of the above over ±0.5 s, ±1 s and ±3 s (share of frames each team was closest / within 1.5 m, share of missing ball, etc.)
- the hysteresis output (one-hot H/A/D)

Model: scikit-learn `HistGradientBoostingClassifier` (200 iterations, 31 leaves, `random_state=0`), trained on every third valid frame of the Metrica games. The training set is mirrored (home and away features and labels swapped) so the model cannot learn "the home team has the ball more often", which is a property of a particular match.

**Step 3: Viterbi decoding.** Three states (H, A, D). Switching H↔A costs 8, entering or leaving D costs 20 (in log-probability units). Costs were selected on out-of-fold predictions: each Metrica game was predicted by a model trained on the other two.

**Step 4: BAR-ATH.** The final model is trained on all three Metrica games and applied once to the BAR-ATH tactical ATD. Pitch size used to convert normalised coordinates to metres: 105 × 68.

## 4. Results on the external bench

Out of sample (each game predicted by a pipeline that never saw it):

| method | G1 | G2 | G3 | mean |
|---|---|---|---|---|
| official baseline (window 50) | 0.402 | 0.390 | 0.357 | 0.383 |
| hysteresis rule | 0.620 | 0.558 | 0.590 | 0.589 |
| classifier, no Viterbi | ~0.27 | ~0.30 | ~0.32 | ~0.30 |
| **classifier + Viterbi (submitted)** | **0.636** | **0.614** | **0.620** | **0.623** |

We did not score our submission on the public 5-minute ground truth. It was used only to check alignment and format, as the rules ask.

On BAR-ATH the submission reports 464 possessions with a mean of 8.9 s, and Barcelona holds about 60% of the alive-ball time.

## 5. Assets used and dropped

| asset | used? | how |
|---|---|---|
| tactical ATD (tracking) | yes | the only input of the submitted pipeline |
| tactical video | yes, experimental | ball detection in frames where the ATD has no ball (section 7). Not in the submitted file |
| homography (tactical) | yes, experimental | to map video detections to pitch coordinates |
| Smart Tagging | no | it has no counterpart in the external data, so we could not validate any use of it |
| broadcast video / ATD | no | not synchronised to the tactical timeline; no time to build a reliable sync |
| team shape features | tried, dropped | width, length, advance and forward speed of each team. Out of sample 0.608 vs 0.623 without them |
| asymmetric dead-ball costs, dead-ball bias | tried, dropped | 0.624 in-sample vs 0.623, but 0.617 when the choice itself was cross-validated: overfitting the bench |

## 6. Training data

No labelled data from the provided game was used anywhere.

| dataset | source | labelled by | amount | used for |
|---|---|---|---|---|
| Metrica Sports sample data, games 1–3 | github.com/metrica-sports/sample-data @ e706dd5 | Metrica Sports (event data) | 3 matches, ~430k frames | possession labels derived from events; training the classifier, selecting every parameter |
| football-ball-detection (pre-trained weights) | roboflow/sports, trained on the Roboflow Universe dataset built from DFL Bundesliga videos | Roboflow | not trained by us | ball detection in the video (experimental only) |

## 7. Handling missing and noisy tracking

**Missing ball.** The ATD has no ball on 41% of graded frames. These gaps are not short or random: there are about 150 of them, with a median of ~10 s and some longer than 3 minutes, and during them the players move at half their usual speed (0.9 vs 1.9 m/s). In Metrica data the same holds: the ball is missing in 78–90% of dead-ball frames and only in 14–19% of alive frames. So the missing ball is mostly dead ball, and the model uses both the gap and its length as evidence. Note that the official baseline already exploits this (no ball → nobody owns it → D), so it is not an advantage by itself.

**Video ball detection (not in the submission).** We ran the pre-trained detector on the 64,643 frames without an ATD ball, plus 1 in 25 frames with one (only as an automatic agreement check). The ball is 4–9 px wide in the tactical view, so each frame is split into eight 640-px tiles. When the ATD has the ball, the detector's best candidate is within 2 m of it in 59% of frames. About half of all candidates are fixed objects (penalty spots, the centre spot, goal posts, an object near the touchline), which we remove with a physical rule: anything detected in the same square metre for more than a minute is not a ball in play. After that and a frame-to-frame physical-speed check, 63% of gap frames keep a clean candidate, at a median of 0.8 m from the nearest player. We could not validate its effect on possession because Metrica's sample data has no video, so it is not part of the submitted file.

**Position noise.** We added Gaussian noise to the Metrica positions to see how the hysteresis rule degrades. Small control radii win on clean data, larger ones are more robust to noise. We measured the frame-to-frame jitter of the BAR-ATH ATD (median second difference of position): players 0.0014 m, ball 0.011 m, both far below what even 0.3 m of white noise produces. We kept r = 1.0 m, which is within 0.007 of the best on clean data and more robust if the noise is higher than measured.

## 8. Possession rules we implemented

- **Control.** A team controls the ball when its nearest player is within 1 m of the ball.
- **Change of possession.** Requires the other team to control the ball for at least 0.32 s (8 frames). A touch, a deflection or a block by the opponent that is not followed by control does not change possession.
- **Loose balls and long passes.** While nobody controls the ball, possession stays with the last team that did. A pass that travels 40 m is still the passing team's possession until someone controls it.
- **Contested balls.** Possession does not change during a duel until one side keeps the ball for the threshold time. If the defending team wins it, the change is placed when its control starts.
- **Dead ball.** The ball is dead when it goes out of the pitch lines, and also when it is missing from the tracking in a context the model recognises as a stoppage (long gap, players slowing down). In the final decoder these are probabilities, not hard rules.
- **Restarts.** After a dead ball, possession goes to the first team that controls the ball. We do not label who owns a dead ball, as the task specifies.

<analyst: add here how we treat goalkeeper saves, aerial duels and throw-ins after reviewing the video>

## 9. Limitations

- **The bench is not the challenge's ground truth.** Our labels come from Metrica's event data, the challenge's from Metrica's corrected tracking. Boundaries, especially around dead ball, will differ.
- **Three matches.** All parameters come from three games. The leave-one-game-out spread (0.614–0.636) suggests stability, but it is a small sample.
- **Systematic tracking error.** We measured jitter, not bias. If the BAR-ATH ball position is consistently offset, the 1 m control radius could be too tight.
- **Alive ball without tracking.** The model tends to call D when the ball is missing but play continues. This is where most of the remaining error is on the bench.
- **Unused signals.** Smart Tagging and the video detections could help exactly in those frames, but we had no external data to validate them, so we left them out rather than add an untested component.

With more time: an external dataset with video, to validate the ball detector end to end, and a semi-Markov decoder with learned possession durations.

## 10. Reproduction

Requirements: Python 3.11+ (tested on 3.13), git, and the challenge data placed in `data/tactical/` with its original file names.

```bash
bash reproducir.sh <team_name>
```

This creates a virtual environment with pinned versions (`requirements-nuestro.txt`: numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1, kloppy 3.18.0), downloads Metrica's sample data at a fixed commit, trains the model, writes `outputs/<team_name>.csv` and runs the official validator. It takes about 4 minutes on a laptop. We ran it twice from a clean copy and obtained a byte-identical file (md5 `bf458c4d098e0c0cc823bae755b03b5d`).

The bench results in section 4 can be reproduced with `cd src && python calibrar_histeresis.py` (hysteresis) and `python src/generar_v1.py` (prints the out-of-fold scores).

## 11. Use of AI tools

We used Claude (Anthropic) as a development assistant for code and analysis. Following the organisers' rule clarification of 11 November, which allows uploading the provided data to AI services, some of the tracking data was processed with it. The pipeline itself uses no LLM.
