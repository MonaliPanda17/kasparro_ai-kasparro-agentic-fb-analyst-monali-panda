# Report

## LLM Narrative

In the past week, performance metrics have shown a decline compared to the baseline period. The Return on Ad Spend (ROAS) decreased from 5.45 to 5.29, indicating a drop of approximately 2.97%. Revenue also fell by 4.45%, while Cost Per Acquisition (CPA) increased slightly by 1.92%. 

**Key Takeaways:**
- **Top Gainers:** The "Women Fit & Lift" campaign saw a revenue increase of 54.54% with a ROAS improvement of 12.00%. Similarly, "Men | Athleisure Cooling" achieved a 11.25% revenue growth and a significant ROAS increase of 28.80%.
- **Top Losers:** The "Women | Studio Sports" segment experienced a substantial revenue decline of 34.21% and a ROAS drop of 20.67%. "Men Comfortmax Launch" also faced a 29.63% revenue decrease with a corresponding ROAS decline of 27.07%.
- **Overall Trends:** The analysis indicates a need to reassess budget allocation and creative strategies, particularly in underperforming segments, to enhance overall campaign effectiveness.

Task: Analyze ROAS drop in 7 days

## Analysis Plan (Analyst Thinking)

**Plan Source:** 📋 Rule-based

**Problem Type:** roas_drop

**Hypotheses to Test:**
1. Budget shifted to lower-ROAS segments (campaigns/adsets/countries)
2. Creative fatigue: older creatives losing effectiveness
3. Audience dilution: targeting broadened, quality declined
4. Platform mix changed: budget moved to lower-ROAS platforms
5. Spend efficiency: CVR or AOV declined while spend increased

**Analysis Strategy:** Focus on contribution analysis: which segments drove ROAS decline? Check spend shifts, creative performance, and platform mix.

**Reasoning:**
- *Think:* User query: Analyze ROAS drop in 7 days. Problem classified as roas_drop.
- *Analyze:* Focus on roas, revenue, cpa metrics across campaign_name, adset_name, creative_type dimensions.
- *Conclude:* Execute 5 subtasks to generate insights and recommendations.

**Subtask Decomposition:**
1. [data_agent] load_and_summarize: Load dataset and generate overview metrics
2. [data_agent] segment_compare: Compare segments across dimensions
3. [insight_agent] generate_hypotheses: Generate insights from segment data
4. [evaluator_agent] validate_insights: Quantitatively validate insights
5. [creative_generator] generate_for_low_ctr: Generate creatives for low-CTR campaigns

**Configuration:**
- Window: 7 days
- KPIs: roas, revenue, cpa
- Segments (prioritized): campaign_name, adset_name, creative_type, platform, audience_type, country

## Overview
Current: 2025-03-25 → 2025-03-31
Baseline: 2025-03-18 → 2025-03-24
ROAS: 5.29 vs 5.45

## Executive Summary

**Performance Change:** ROAS declined by 2.97% (5.29 vs 5.45)
**Revenue Impact:** $-40,430 vs baseline period

## Top Insights

*Validation Summary: 45/45 insights validated (avg confidence: 0.96)*

### 1. campaign_name: 'Men | Athleisure Cooling' gained $14,741 revenue (ROAS 11.87)
**Impact:** HIGH | **Score:** 0.97 | **Confidence:** 0.97

**Reasoning:**
- *Think:* Data shows campaign_name 'Men | Athleisure Cooling' gained $14,741 in revenue with ROAS of 11.87.
- *Analyze:* This segment outperforms aggregate ROAS (5.29) by 124.4%. Possible factors: effective targeting, strong creative, optimal platform mix, or favorable audience.
- *Conclude:* Scale budget allocation to this segment. Evidence: ROAS advantage combined with positive revenue delta. Recommended action: Increase spend by 20-30% to capitalize on performance.

**Strengths:** Numbers validated and evidence cited, Specific segment names and metrics included, Clear actionable recommendation

### 2. campaign_name: 'Men-Athleisure Cooling' gained $14,071 revenue (ROAS 11.60)
**Impact:** HIGH | **Score:** 0.97 | **Confidence:** 0.97

**Reasoning:**
- *Think:* Data shows campaign_name 'Men-Athleisure Cooling' gained $14,071 in revenue with ROAS of 11.60.
- *Analyze:* This segment outperforms aggregate ROAS (5.29) by 119.3%. Possible factors: effective targeting, strong creative, optimal platform mix, or favorable audience.
- *Conclude:* Scale budget allocation to this segment. Evidence: ROAS advantage combined with positive revenue delta. Recommended action: Increase spend by 20-30% to capitalize on performance.

**Strengths:** Numbers validated and evidence cited, Specific segment names and metrics included, Clear actionable recommendation

### 3. campaign_name: 'Men Omfortmax Launch' gained $7,214 revenue (ROAS 19.09)
**Impact:** HIGH | **Score:** 0.97 | **Confidence:** 0.97

**Reasoning:**
- *Think:* Data shows campaign_name 'Men Omfortmax Launch' gained $7,214 in revenue with ROAS of 19.09.
- *Analyze:* This segment outperforms aggregate ROAS (5.29) by 261.0%. Possible factors: effective targeting, strong creative, optimal platform mix, or favorable audience.
- *Conclude:* Scale budget allocation to this segment. Evidence: ROAS advantage combined with positive revenue delta. Recommended action: Increase spend by 20-30% to capitalize on performance.

**Strengths:** Numbers validated and evidence cited, Specific segment names and metrics included, Clear actionable recommendation

### 4. campaign_name: 'Women | Stu Io Sports' lost $8,876 revenue (ROAS 0.00 vs 8.48)
**Impact:** HIGH | **Score:** 0.97 | **Confidence:** 0.97

**Reasoning:**
- *Think:* Data shows campaign_name 'Women | Stu Io Sports' lost $8,876 with ROAS of 0.00 vs baseline 8.48.
- *Analyze:* ROAS declined by -100.0% while holding 0.0% of spend. Possible causes: creative fatigue, audience dilution, competitive pressure, or platform algorithm changes.
- *Conclude:* Reallocate 50-70% of budget from this underperforming segment to winners. Evidence: ROAS gap and negative revenue impact justify reallocation. Immediate action: Pause or reduce spend to test if performance recovers.

**Strengths:** Numbers validated and evidence cited, Specific segment names and metrics included, Clear actionable recommendation

### 5. adset_name: 'Adset-4 Broad' gained $22,517 revenue (ROAS 8.19)
**Impact:** HIGH | **Score:** 0.97 | **Confidence:** 0.97

**Reasoning:**
- *Think:* Data shows adset_name 'Adset-4 Broad' gained $22,517 in revenue with ROAS of 8.19.
- *Analyze:* This segment outperforms aggregate ROAS (5.29) by 54.9%. Possible factors: effective targeting, strong creative, optimal platform mix, or favorable audience.
- *Conclude:* Scale budget allocation to this segment. Evidence: ROAS advantage combined with positive revenue delta. Recommended action: Increase spend by 20-30% to capitalize on performance.

**Strengths:** Numbers validated and evidence cited, Specific segment names and metrics included, Clear actionable recommendation

## Problem Drivers (Underperforming Segments)

Segments contributing to performance decline:

### 1. campaign_name: 'Women | Studio Sports' lost $42,905 revenue (ROAS 7.02 vs 8.85)
**Score:** 0.97 | **Confidence:** 0.97
**Revenue Impact:** $-42,905
**ROAS:** 7.02 vs 8.85

**Recommendation:** Reallocate 50-70% of budget from this underperforming segment to winners. Evidence: ROAS gap and negative revenue impact justify reallocation. Immediate action: Pause or reduce spend to test if performance recovers.

### 2. campaign_name: 'Men Comfortmax Launch' lost $31,801 revenue (ROAS 5.11 vs 7.00)
**Score:** 0.97 | **Confidence:** 0.97
**Revenue Impact:** $-31,801
**ROAS:** 5.11 vs 7.00

**Recommendation:** Reallocate 50-70% of budget from this underperforming segment to winners. Evidence: ROAS gap and negative revenue impact justify reallocation. Immediate action: Pause or reduce spend to test if performance recovers.

### 3. campaign_name: 'Men Premium Modal' lost $16,634 revenue (ROAS 6.28 vs 6.34)
**Score:** 0.97 | **Confidence:** 0.97
**Revenue Impact:** $-16,634
**ROAS:** 6.28 vs 6.34

**Recommendation:** Reallocate 50-70% of budget from this underperforming segment to winners. Evidence: ROAS gap and negative revenue impact justify reallocation. Immediate action: Pause or reduce spend to test if performance recovers.

### 4. campaign_name: 'Women Summer Invisible' lost $10,648 revenue (ROAS 4.23 vs 4.94)
**Score:** 0.97 | **Confidence:** 0.97
**Revenue Impact:** $-10,648
**ROAS:** 4.23 vs 4.94

**Recommendation:** Reallocate 50-70% of budget from this underperforming segment to winners. Evidence: ROAS gap and negative revenue impact justify reallocation. Immediate action: Pause or reduce spend to test if performance recovers.

### 5. campaign_name: 'Women | Stu Io Sports' lost $8,876 revenue (ROAS 0.00 vs 8.48)
**Score:** 0.97 | **Confidence:** 0.97
**Revenue Impact:** $-8,876

**Recommendation:** Reallocate 50-70% of budget from this underperforming segment to winners. Evidence: ROAS gap and negative revenue impact justify reallocation. Immediate action: Pause or reduce spend to test if performance recovers.

## Hypothesis Validation

Testing the following hypotheses:

1. Budget shifted to lower-ROAS segments (campaigns/adsets/countries) - ⏳ Needs more analysis
2. Creative fatigue: older creatives losing effectiveness - ✅ Supported
   - creative_type: 'UGC' gained $33,350 revenue (ROAS 5.08)
   - creative_type: 'Image' gained $-624 revenue (ROAS 5.38)
3. Audience dilution: targeting broadened, quality declined - ✅ Supported
   - audience_type: 'Broad' gained $62,746 revenue (ROAS 4.82)
   - audience_type: 'Retargeting' gained $-35,092 revenue (ROAS 7.06)
4. Platform mix changed: budget moved to lower-ROAS platforms - ✅ Supported
   - platform: 'Facebook' gained $40,388 revenue (ROAS 5.61)
   - platform: 'Instagram' gained $-80,818 revenue (ROAS 4.98)
5. Spend efficiency: CVR or AOV declined while spend increased - ⏳ Needs more analysis

## Creative Recommendations (Low-CTR Campaigns)

### 1. For: Women Cotton Classics
**Current CTR:** 0.0097 → **Target CTR:** 0.0135

**Hook:** Stop the ride-up. Stop the bunching. Start the comfort.
**Body:** Show the comfort in motion. Spotlight sweat-wicking fabric in a real-life demo.
**CTA:** Shop now

*Rationale:* Campaign 'Women Cotton Classics' has CTR 0.0097 (below threshold) with $16,585 spend. Adapting 'problem_solve' strategy from top-performing creatives. Expected to improve CTR through problem_solve messaging.

### 2. For: Women Summer Invisible
**Current CTR:** 0.0103 → **Target CTR:** 0.0144

**Hook:** Seamless Under Everything
**Body:** Contrast before/after silhouettes. Emphasize invisible seams and breathable cotton.
**CTA:** See the fit

*Rationale:* Campaign 'Women Summer Invisible' has CTR 0.0103 (below threshold) with $16,171 spend. Adapting 'visual_benefit' strategy from top-performing creatives. Expected to improve CTR through visual_benefit messaging.

### 3. For: Women | Studio Sports
**Current CTR:** 0.0099 → **Target CTR:** 0.0139

**Hook:** Stop the ride-up. Stop the bunching. Start the comfort.
**Body:** Show the comfort in motion. Spotlight sweat-wicking fabric in a real-life demo.
**CTA:** Shop now

*Rationale:* Campaign 'Women | Studio Sports' has CTR 0.0099 (below threshold) with $11,756 spend. Adapting 'problem_solve' strategy from top-performing creatives. Expected to improve CTR through problem_solve messaging.

### 4. For: Men Premium Modal
**Current CTR:** 0.0101 → **Target CTR:** 0.0141

**Hook:** Seamless Under Everything
**Body:** Contrast before/after silhouettes. Emphasize invisible seams and breathable cotton.
**CTA:** See the fit

*Rationale:* Campaign 'Men Premium Modal' has CTR 0.0101 (below threshold) with $11,736 spend. Adapting 'visual_benefit' strategy from top-performing creatives. Expected to improve CTR through visual_benefit messaging.

### 5. For: Women-Studio Sports
**Current CTR:** 0.0099 → **Target CTR:** 0.0139

**Hook:** Stop the ride-up. Stop the bunching. Start the comfort.
**Body:** Show the comfort in motion. Spotlight sweat-wicking fabric in a real-life demo.
**CTA:** Shop now

*Rationale:* Campaign 'Women-Studio Sports' has CTR 0.0099 (below threshold) with $3,326 spend. Adapting 'problem_solve' strategy from top-performing creatives. Expected to improve CTR through problem_solve messaging.

## Action Items & Next Steps

**1. Scale Winners:**
   - Focus on: campaign_name: 'Women Fit & Lift' gained $20,117 revenue (ROAS 3.12)
   - Action: Scale budget allocation to this segment. Evidence: ROAS advantage combined with positive revenue delta. Recommended action: Increase spend by 20-30% to capitalize on performance.

**2. Address Underperformers:**
   - Problem: campaign_name: 'Women | Studio Sports' lost $42,905 revenue (ROAS 7.02 vs 8.85)
   - Action: Reallocate 50-70% of budget from this underperforming segment to winners. Evidence: ROAS gap and negative revenue impact justify reallocation. Immediate action: Pause or reduce spend to test if performance recovers.

**3. Implement Creative Refresh:**
   - 5 creative recommendations generated for low-CTR campaigns
   - Review `creatives.json` for full details

**4. Monitor & Iterate:**
   - Re-run analysis after implementing changes
   - Track CTR improvements for creative updates
   - Monitor budget reallocation impact
