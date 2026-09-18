#!/usr/bin/env python3
"""Programmatic generator for Milestone 8 Google Forms Apps Script and Specification.

Extracts all stimuli, tasks, dimensions, scales, and presentation schedules strictly
from frozen repository artifacts:
  - docs/M8_EVALUATION.md §12
  - data/benchmarks/m8_human_eval_session_manifest.json
  - data/benchmarks/m8_human_eval_protocol.md
  - data/benchmarks/m8_human_eval_instrument.md

Outputs:
  - scripts/create_m8_google_forms.js (Executable Google Apps Script for script.google.com)
  - data/benchmarks/m8_google_forms_specification.md (Complete human-readable specification)
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_session_manifest.json"
PROTOCOL_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_protocol.md"
INSTRUMENT_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_instrument.md"
CHECKLIST_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_session_checklist.md"

OUTPUT_JS_PATH = REPO_ROOT / "scripts" / "create_m8_google_forms.js"
OUTPUT_SPEC_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_google_forms_specification.md"


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def extract_stimulus_cards(protocol_text: str) -> dict[str, dict[str, str]]:
    """Extract Format A and Format B YAML blocks for each comparison from protocol.md."""
    pattern = re.compile(
        r"### Comparison (\d+):[^\n]*\n"
        r".*?#### Format A: Plain Metadata Card\s*```yaml\s*(.*?)\s*```"
        r".*?#### Format B: Evidence-Backed RecommendationCard\s*```yaml\s*(.*?)\s*```",
        re.DOTALL,
    )
    matches = pattern.findall(protocol_text)
    if len(matches) != 7:
        raise ValueError(f"Expected 7 comparisons in protocol.md, found {len(matches)}")

    cards_by_comp: dict[str, dict[str, str]] = {}
    for comp_num_str, format_a_yaml, format_b_yaml in matches:
        comp_id = f"comp_{comp_num_str}"
        # Validate Format A has exactly 4 fields
        a_lines = [line.strip() for line in format_a_yaml.strip().splitlines() if line.strip()]
        a_keys = [line.split(":")[0].strip() for line in a_lines]
        if a_keys != ["name", "source", "modality", "size"]:
            raise ValueError(f"Format A keys in {comp_id} do not match [name, source, modality, size]: {a_keys}")

        # Strip internal hash identifiers (card_id and dataset_id) from Format B for participant view
        b_lines = format_b_yaml.strip().splitlines()
        b_filtered = [
            line for line in b_lines
            if not line.strip().startswith("card_id:") and not line.strip().startswith("dataset_id:")
        ]
        cards_by_comp[comp_id] = {
            "format_a": format_a_yaml.strip(),
            "format_b_full": format_b_yaml.strip(),
            "format_b_participant": "\n".join(b_filtered).strip(),
        }

    return cards_by_comp


def get_task_modality_label(task_name: str) -> str:
    mapping = {
        "task_sentiment_binary": "Text Classification (Modality: Text)",
        "task_tabular_titanic": "Tabular Classification (Modality: Tabular)",
        "task_image_cifar": "Image Classification (Modality: Image)",
    }
    if task_name not in mapping:
        raise ValueError(f"Unknown task_name: {task_name}")
    return mapping[task_name]


def generate_google_apps_script(
    manifest: dict[str, Any],
    cards: dict[str, dict[str, str]],
) -> str:
    """Generate turnkey Google Apps Script for FormApp."""
    comparisons = manifest["comparisons"]

    js_comparisons: list[dict[str, Any]] = []
    for c in comparisons:
        cid = c["comparison_id"]
        c_cards = cards[cid]
        js_comparisons.append({
            "comparison_id": cid,
            "task_name": c["task_name"],
            "task_label": get_task_modality_label(c["task_name"]),
            "dataset_id": c["dataset_id"],
            "dataset_name": c["dataset_name"],
            "format_a": c_cards["format_a"],
            "format_b": c_cards["format_b_participant"],
            "presentation_order": c["presentation_order"],
        })

    study_config = {
        "study_id": "m8-human-eval-v1",
        "form_display_title": "Dataset Discovery Tool Evaluation",
        "intro_description": (
            "Evaluation of Dataset Information Representations for Machine Learning Tasks\n\n"
            "Purpose of the Study:\n"
            "In this study, you will evaluate different representations of dataset information for machine learning tasks. "
            "When selecting a dataset for a real-world task, practitioners must assess whether a candidate dataset fits "
            "their technical requirements, data modality, quality expectations, and licensing constraints.\n\n"
            "Your Role as an Evaluator:\n"
            "You will be presented with 7 comparison sets spanning three machine learning tasks "
            "(Text Classification, Tabular Classification, and Image Classification).\n"
            "For each comparison:\n"
            "1. Read the Task Description and requirements carefully.\n"
            "2. Examine Card 1 and provide your ratings independently across three dimensions.\n"
            "3. Examine Card 2 (an alternative representation of the same dataset) and provide your ratings independently across the same three dimensions.\n\n"
            "Neutrality & Blinding Guidelines:\n"
            "- Card representations are generated by alternative automated tooling: You will not be told which algorithmic pipeline or source generated which card.\n"
            "- Rate each card on its own merits: Do not assume that one card format is intended to be 'better' or 'worse'. Provide honest, calibrated assessments based strictly on the information presented on each card.\n"
            "- Presentation order is randomized: The order in which formats appear (Card 1 vs Card 2) varies across comparisons and raters to prevent order bias.\n\n"
            "Response Scale Anchors (1-5 Likert Scale):\n"
            "1 = Strongly Disagree (The card fails completely on this dimension; information is absent, unreliable, or uninformative.)\n"
            "2 = Disagree (The card is substantially deficient; important information is missing or unclear.)\n"
            "3 = Neutral / Undecided (Borderline; the card provides basic facts but leaves key questions unanswered.)\n"
            "4 = Agree (The card satisfies this dimension well; information is clear, credible, and informative.)\n"
            "5 = Strongly Agree (The card excels on this dimension; provides thorough, clear, credible, and immediately actionable detail.)\n\n"
            "Voluntary Participation & Anonymity:\n"
            "This evaluation is conducted for an academic capstone research project. Your responses are anonymous and will be analyzed only in aggregate. "
            "No personally identifiable information is collected. Participation is voluntary; you may withdraw at any time."
        ),
        "confirmation_message": "Thank you for completing the evaluation. Your responses have been successfully recorded.",
        "dimensions": [
            {
                "id": "trust",
                "title": "Trust",
                "prompt": '"I trust that this card provides a reliable, credible, and verifiable representation of the dataset\'s characteristics and suitability for the task."',
                "type": "scale",
                "required": True,
                "min": 1,
                "max": 5,
                "minLabel": "Strongly Disagree",
                "maxLabel": "Strongly Agree",
            },
            {
                "id": "understanding",
                "title": "Understanding",
                "prompt": '"I understand why this dataset was surfaced and how it connects to the specific technical requirements of the task."',
                "type": "scale",
                "required": True,
                "min": 1,
                "max": 5,
                "minLabel": "Strongly Disagree",
                "maxLabel": "Strongly Agree",
            },
            {
                "id": "actionability",
                "title": "Actionability",
                "prompt": '"This card provides sufficient and relevant information for me to make an informed decision on whether to adopt, further inspect, or reject this dataset for the task."',
                "type": "scale",
                "required": True,
                "min": 1,
                "max": 5,
                "minLabel": "Strongly Disagree",
                "maxLabel": "Strongly Agree",
            },
            {
                "id": "comments",
                "title": "Comments (Optional)",
                "prompt": "Optional notes, observations, or rationale regarding this card.",
                "type": "text",
                "required": False,
            },
        ],
        "comparisons": js_comparisons,
    }

    config_json = json.dumps(study_config, indent=2)

    script_content = f"""/**
 * Milestone 8 Human Evaluation: Automated Google Forms Generator
 *
 * Governing Protocol: docs/M8_EVALUATION.md §12, data/benchmarks/m8_human_eval_protocol.md
 * Freeze Commit: c5bdc0c1bd458c3d71a5181fa67232c831c3804c
 * Seed: 20260914 (outcome-independent deterministic presentation schedule)
 *
 * Usage Instructions:
 * 1. Open Google Apps Script: https://script.google.com/
 * 2. Click "+ New project".
 * 3. Replace all default code in Code.gs with the entirety of this script.
 * 4. In the function dropdown at the top, select "createAllM8Forms".
 * 5. Click "Run" (and grant authorization when prompted by Google).
 * 6. View the Execution Log (bottom panel):
 *    The Edit URLs and Published View URLs for rater_1, rater_2, and rater_3 will be logged.
 * 7. Copy the Published URL for each rater and distribute.
 */

var STUDY_CONFIG = {config_json};

/**
 * Creates all 3 independent Google Forms in Google Drive and logs their URLs.
 */
function createAllM8Forms() {{
  var raters = ["rater_1", "rater_2", "rater_3"];
  var results = [];

  for (var i = 0; i < raters.length; i++) {{
    var raterId = raters[i];
    Logger.log(">>> Building form for " + raterId + "...");
    var result = buildFormForRater(raterId);
    results.push(result);
  }}

  Logger.log("\\n========================================================");
  Logger.log("ALL 3 FORMS SUCCESSFULLY GENERATED");
  Logger.log("========================================================");
  for (var j = 0; j < results.length; j++) {{
    var res = results[j];
    Logger.log("\\nRATER ID: " + res.raterId);
    Logger.log("  Drive File Name : " + res.driveFileName);
    Logger.log("  Published URL   : " + res.publishedUrl);
    Logger.log("  Edit / Admin URL: " + res.editUrl);
  }}
  Logger.log("========================================================\\n");
  return results;
}}

function createRater1Form() {{ return buildFormForRater("rater_1"); }}
function createRater2Form() {{ return buildFormForRater("rater_2"); }}
function createRater3Form() {{ return buildFormForRater("rater_3"); }}

/**
 * Builds an independent Google Form for a specific rater.
 */
function buildFormForRater(raterId) {{
  var driveFileName = "Dataset Discovery Tool Evaluation - " + raterId.toUpperCase();
  var form = FormApp.create(driveFileName);

  // Set participant-facing title and briefing
  form.setTitle(STUDY_CONFIG.form_display_title);
  form.setDescription(STUDY_CONFIG.intro_description);

  // Anti-bias, anonymity, and deterministic schedule settings
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false);
  form.setShuffleQuestions(false);
  form.setConfirmationMessage(STUDY_CONFIG.confirmation_message);

  try {{
    form.setRequireLogin(false);
  }} catch (e) {{
    // Workspace-specific method, safe to ignore on personal accounts
  }}

  var comparisons = STUDY_CONFIG.comparisons;
  for (var i = 0; i < comparisons.length; i++) {{
    var comp = comparisons[i];
    var compIndex = i + 1;
    var order = comp.presentation_order[raterId]; // "A_first" or "B_first"

    var card1Content, card2Content;
    if (order === "B_first") {{
      card1Content = comp.format_b;
      card2Content = comp.format_a;
    }} else if (order === "A_first") {{
      card1Content = comp.format_a;
      card2Content = comp.format_b;
    }} else {{
      throw new Error("Invalid order for " + raterId + " in " + comp.comparison_id + ": " + order);
    }}

    // Add Section Break (Page) for this comparison
    var pageBreak = form.addPageBreakItem();
    pageBreak.setTitle("Comparison " + compIndex + " of 7: " + comp.dataset_name);
    pageBreak.setHelpText(
      "Task: " + comp.task_label + "\\n" +
      "Dataset: " + comp.dataset_name + "\\n\\n" +
      "Please review Card 1 and Card 2 below and provide independent ratings for each card."
    );

    // --- CARD 1 ---
    var card1Header = form.addSectionHeaderItem();
    card1Header.setTitle("Card 1");
    card1Header.setHelpText(card1Content);
    addRatingItemsToForm(form, "Card 1");

    // --- CARD 2 ---
    var card2Header = form.addSectionHeaderItem();
    card2Header.setTitle("Card 2");
    card2Header.setHelpText(card2Content);
    addRatingItemsToForm(form, "Card 2");
  }}

  var editUrl = form.getEditUrl();
  var publishedUrl = form.getPublishedUrl();

  Logger.log("Form created for " + raterId + ": " + publishedUrl);

  return {{
    raterId: raterId,
    driveFileName: driveFileName,
    editUrl: editUrl,
    publishedUrl: publishedUrl
  }};
}}

/**
 * Adds the 3 Likert scale items and 1 optional comments item to a card section.
 */
function addRatingItemsToForm(form, cardLabel) {{
  var dims = STUDY_CONFIG.dimensions;
  for (var k = 0; k < dims.length; k++) {{
    var dim = dims[k];
    if (dim.type === "scale") {{
      var scaleItem = form.addScaleItem();
      scaleItem.setTitle(cardLabel + " — " + dim.title + ": " + dim.prompt);
      scaleItem.setBounds(dim.min, dim.max);
      scaleItem.setLabels(dim.minLabel, dim.maxLabel);
      scaleItem.setRequired(dim.required);
    }} else if (dim.type === "text") {{
      var textItem = form.addParagraphTextItem();
      textItem.setTitle(cardLabel + " — " + dim.title);
      textItem.setHelpText(dim.prompt);
      textItem.setRequired(dim.required);
    }}
  }}
}}

// CommonJS export for automated validation in Node.js
if (typeof module !== 'undefined' && module.exports) {{
  module.exports = {{
    STUDY_CONFIG: STUDY_CONFIG,
    createAllM8Forms: createAllM8Forms,
    buildFormForRater: buildFormForRater,
    addRatingItemsToForm: addRatingItemsToForm
  }};
}}
"""
    return script_content


def generate_specification_markdown(
    manifest: dict[str, Any],
    cards: dict[str, dict[str, str]],
) -> str:
    """Generate detailed specification document."""
    comparisons = manifest["comparisons"]

    order_table_rows = []
    for c in comparisons:
        cid = c["comparison_id"]
        ds = c["dataset_name"]
        r1 = "Card 1 = Format B, Card 2 = Format A" if c["presentation_order"]["rater_1"] == "B_first" else "Card 1 = Format A, Card 2 = Format B"
        r2 = "Card 1 = Format B, Card 2 = Format A" if c["presentation_order"]["rater_2"] == "B_first" else "Card 1 = Format A, Card 2 = Format B"
        r3 = "Card 1 = Format B, Card 2 = Format A" if c["presentation_order"]["rater_3"] == "B_first" else "Card 1 = Format A, Card 2 = Format B"
        order_table_rows.append(f"| `{cid}` | `{ds}` | {r1} | {r2} | {r3} |")
    order_table_str = "\n".join(order_table_rows)

    comp_sections = []
    for i, c in enumerate(comparisons, 1):
        cid = c["comparison_id"]
        c_cards = cards[cid]
        task_label = get_task_modality_label(c["task_name"])
        fa = c_cards["format_a"]
        fb = c_cards["format_b_participant"]
        orders = c["presentation_order"]

        sec = f"""### Comparison {i} of 7: {c['dataset_name']} (`{cid}`)

* **Task Context:** `Task: {task_label}`
* **Dataset Under Evaluation:** `{c['dataset_name']}` (`{c['dataset_id']}`)
* **Presentation Schedule:**
  - `rater_1`: `{orders['rater_1']}` ({'Card 1 = Format B, Card 2 = Format A' if orders['rater_1'] == 'B_first' else 'Card 1 = Format A, Card 2 = Format B'})
  - `rater_2`: `{orders['rater_2']}` ({'Card 1 = Format B, Card 2 = Format A' if orders['rater_2'] == 'B_first' else 'Card 1 = Format A, Card 2 = Format B'})
  - `rater_3`: `{orders['rater_3']}` ({'Card 1 = Format B, Card 2 = Format A' if orders['rater_3'] == 'B_first' else 'Card 1 = Format A, Card 2 = Format B'})

#### Format A Content (Plain Metadata Card):
```yaml
{fa}
```

#### Format B Content (Participant-Facing Recommendation Card, hashes excluded):
```yaml
{fb}
```

#### Questionnaire Items (Identical for Card 1 and Card 2):
1. **Trust (Linear Scale 1-5, Required):**
   - Statement: *"I trust that this card provides a reliable, credible, and verifiable representation of the dataset's characteristics and suitability for the task."*
   - Anchors: `1 = Strongly Disagree`, `5 = Strongly Agree`
2. **Understanding (Linear Scale 1-5, Required):**
   - Statement: *"I understand why this dataset was surfaced and how it connects to the specific technical requirements of the task."*
   - Anchors: `1 = Strongly Disagree`, `5 = Strongly Agree`
3. **Actionability (Linear Scale 1-5, Required):**
   - Statement: *"This card provides sufficient and relevant information for me to make an informed decision on whether to adopt, further inspect, or reject this dataset for the task."*
   - Anchors: `1 = Strongly Disagree`, `5 = Strongly Agree`
4. **Comments (Paragraph Text, Optional):**
   - Title: `Comments (Optional)`
   - Help text: `Optional notes, observations, or rationale regarding this card.`
"""
        comp_sections.append(sec)

    all_comp_sections_str = "\n---\n\n".join(comp_sections)

    spec_md = f"""# Milestone 8 Human Evaluation: Google Forms Specification & Operator Guide

> **Study Identifier:** `m8-human-eval-v1`
> **Authoritative Freeze Commit:** `c5bdc0c1bd458c3d71a5181fa67232c831c3804c`
> **Governing Documents:** `docs/M8_EVALUATION.md` §12, `data/benchmarks/m8_human_eval_protocol.md`, `data/benchmarks/m8_human_eval_instrument.md`, `data/benchmarks/m8_human_eval_session_manifest.json`
> **Implementation Artifacts:**
> - Turnkey Google Apps Script: `scripts/create_m8_google_forms.js`
> - Data-Capture Tool: `scripts/capture_m8_human_eval_response.py`
> - Responses Target: `data/benchmarks/m8_human_eval_responses.csv` (strictly header-only prior to authorized sessions)

---

## 1. Study Architecture & Protocol Invariants

1. **One Independent Form per Rater:**
   - Because the presentation order is **pre-committed and deterministic** (random seed `20260914`), Google Forms' built-in random shuffle must **not** be used.
   - Three independent forms are prepared:
     - `Dataset Discovery Tool Evaluation - RATER_1` (for project author, disclosed as non-blind)
     - `Dataset Discovery Tool Evaluation - RATER_2` (for independent external evaluator, blind)
     - `Dataset Discovery Tool Evaluation - RATER_3` (for secondary independent external evaluator, blind)
   - To participants, each form displays the identical neutral title: **`Dataset Discovery Tool Evaluation`**.

2. **Form Structure & Item Accounting:**
   - 1 Briefing / Intro Section (verbatim instructions, blinding guidelines, 5-point scale anchors, voluntary consent blurb).
   - 7 Comparison Sections (Pages 2 through 8), one comparison per page.
   - Per Comparison: 2 Cards (Card 1 and Card 2).
   - Per Card: 3 Likert Scale questions (1-5, Required) + 1 Comment field (Optional).
   - **Per Form Response Fields:** $7 \\times 2 \\times 4 = 56 \\text{{ fields}}$ ($42 \\text{{ required Likert scales}} + 14 \\text{{ optional comments}}$).
   - **Total Responses Logged upon Study Completion:**
     - 2 Raters: 28 rows in `m8_human_eval_responses.csv` (84 Likert ratings).
     - 3 Raters: 42 rows in `m8_human_eval_responses.csv` (126 Likert ratings).

3. **Anti-Bias & Privacy Settings:**
   - Collect email addresses: **OFF**
   - Limit to 1 response (sign-in required): **OFF**
   - Shuffle question order: **OFF**
   - Confirmation message: *"Thank you for completing the evaluation. Your responses have been successfully recorded."*
   - Cards are labeled strictly **"Card 1"** and **"Card 2"**.
   - No evaluative labels ("Format A", "Format B", "baseline", "system", "recommendation").
   - Internal hashes (`card_id`, `dataset_id`) are excluded from rater view.

---

## 2. Pre-Committed Presentation Schedule Matrix (Seed `20260914`)

| Comparison ID | Dataset Name | Rater 1 Presentation | Rater 2 Presentation | Rater 3 Presentation |
| :--- | :--- | :--- | :--- | :--- |
{order_table_str}

---

## 3. How to Deploy via Google Apps Script (Automated 1-Click Setup)

1. Open your browser and navigate to [Google Apps Script](https://script.google.com/).
2. Click **+ New project**.
3. Clear the default `myFunction` code in the editor.
4. Copy the entire contents of [`scripts/create_m8_google_forms.js`](../../scripts/create_m8_google_forms.js) and paste into the editor.
5. In the toolbar function dropdown, ensure **`createAllM8Forms`** is selected.
6. Click **Run**.
7. Grant Google OAuth permissions when prompted (this allows the script to create Google Forms in your Google Drive).
8. View the **Execution log** at the bottom of the editor.
   The script will log:
   - Form 1 (`rater_1`): Published URL and Edit URL
   - Form 2 (`rater_2`): Published URL and Edit URL
   - Form 3 (`rater_3`): Published URL and Edit URL
9. Copy each rater's **Published URL** and provide it to the respective evaluator.

---

## 4. Participant-Facing Briefing Text (Verbatim Instrument §1)

```
Purpose of the Study:
In this study, you will evaluate different representations of dataset information for machine learning tasks. When selecting a dataset for a real-world task, practitioners must assess whether a candidate dataset fits their technical requirements, data modality, quality expectations, and licensing constraints.

Your Role as an Evaluator:
You will be presented with 7 comparison sets spanning three machine learning tasks (Text Classification, Tabular Classification, and Image Classification).
For each comparison:
1. Read the Task Description and requirements carefully.
2. Examine Card 1 and provide your ratings independently across three dimensions.
3. Examine Card 2 (an alternative representation of the same dataset) and provide your ratings independently across the same three dimensions.

Neutrality & Blinding Guidelines:
- Card representations are generated by alternative automated tooling: You will not be told which algorithmic pipeline or source generated which card.
- Rate each card on its own merits: Do not assume that one card format is intended to be 'better' or 'worse'. Provide honest, calibrated assessments based strictly on the information presented on each card.
- Presentation order is randomized: The order in which formats appear (Card 1 vs Card 2) varies across comparisons and raters to prevent order bias.

Response Scale Anchors:
1 = Strongly Disagree (The card fails completely on this dimension; information is absent, unreliable, or uninformative.)
2 = Disagree (The card is substantially deficient; important information is missing or unclear.)
3 = Neutral / Undecided (Borderline; the card provides basic facts but leaves key questions unanswered.)
4 = Agree (The card satisfies this dimension well; information is clear, credible, and informative.)
5 = Strongly Agree (The card excels on this dimension; provides thorough, clear, credible, and immediately actionable detail.)

Voluntary Participation & Anonymity:
This evaluation is conducted for an academic capstone research project. Your responses are anonymous and will be analyzed only in aggregate. No personally identifiable information is collected. Participation is voluntary; you may withdraw at any time.
```

---

## 5. Detailed Comparison Stimuli (All 7 Sections)

{all_comp_sections_str}

---

## 6. Response Ingestion & Transcription Procedure

Following session completion, do **not** manually alter `data/benchmarks/m8_human_eval_responses.csv`.
Route each observation row through the audited capture utility:

```bash
python3 scripts/capture_m8_human_eval_response.py \\
  --rater-id <rater_1|rater_2|rater_3> \\
  --task-name <task_sentiment_binary|task_tabular_titanic|task_image_cifar> \\
  --comparison-id <comp_1..comp_7> \\
  --dataset-id <ds_id> \\
  --format-presented <format_a_plain|format_b_evidence> \\
  --presentation-order <first|second> \\
  --trust-score <1-5> \\
  --understanding-score <1-5> \\
  --actionability-score <1-5> \\
  --notes "<optional notes>"
```

### Verified Mapping Table for Transcription:

| comparison_id | task_name | dataset_id | Card 1 (first) Format (R1 / R2 / R3) | Card 2 (second) Format (R1 / R2 / R3) |
| :--- | :--- | :--- | :--- | :--- |
| `comp_1` | `task_sentiment_binary` | `ds_3e424a817c66aab45e96797a` | B / B / A | A / A / B |
| `comp_2` | `task_sentiment_binary` | `ds_c9a42d9bd6268ce4a4cf6061` | B / A / B | A / B / A |
| `comp_3` | `task_tabular_titanic` | `ds_a67e752b027f81f22083533c` | B / B / B | A / A / A |
| `comp_4` | `task_tabular_titanic` | `ds_9f128b3a604eed483953e7f8` | A / A / B | B / B / A |
| `comp_5` | `task_tabular_titanic` | `ds_bdf285c7cdab311e6bd061ed` | B / B / B | A / A / A |
| `comp_6` | `task_image_cifar` | `ds_40356f676278cb9903556c6e` | B / A / A | A / B / B |
| `comp_7` | `task_image_cifar` | `ds_4e61d125afd0915cf8dcb4c6` | A / A / B | B / B / A |

---

## 7. Pre-Session Operator Checklist

- [ ] Apps Script run in `script.google.com` and all 3 form URLs recorded.
- [ ] Confirmed settings on each form:
  - Collect emails: OFF
  - Limit to 1 response: OFF
  - Shuffle questions: OFF
- [ ] Form titles displayed to participants: `Dataset Discovery Tool Evaluation`.
- [ ] `data/benchmarks/m8_human_eval_responses.csv` is confirmed header-only (zero participant rows).
- [ ] Rater IDs assigned privately by operator (`rater_1` = author, `rater_2` = independent evaluator, `rater_3` = optional second independent evaluator).
"""
    return spec_md


def main() -> None:
    manifest = load_manifest()
    protocol_text = PROTOCOL_PATH.read_text(encoding="utf-8")
    cards = extract_stimulus_cards(protocol_text)

    js_code = generate_google_apps_script(manifest, cards)
    OUTPUT_JS_PATH.write_text(js_code, encoding="utf-8")
    print(f"Generated Google Apps Script: {OUTPUT_JS_PATH} ({len(js_code.splitlines())} lines)")

    spec_md = generate_specification_markdown(manifest, cards)
    OUTPUT_SPEC_PATH.write_text(spec_md, encoding="utf-8")
    print(f"Generated Specification: {OUTPUT_SPEC_PATH} ({len(spec_md.splitlines())} lines)")


if __name__ == "__main__":
    main()
