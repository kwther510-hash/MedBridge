# MedBridge Content Guide

You never need to edit app.py to add content.

## Add a new week
1. Copy an existing week file in `data/` and rename it (any name ending in `.json`, e.g. `UpperLimb_Week2.json`).
2. Change `"week"` to the new number (a number, not text) and keep `"region"` the same (e.g. `"Upper Limb"`).
3. Replace the content. Sections are optional; a tab appears only if its list is not empty:
   - `case_mappings` (clinical cases)
   - `lecture_mcqs`
   - `quick_recall`
4. Commit and push. The week appears automatically in the Upper Limb module.
5. A new region (e.g. `"Lower Limb"`) creates a new module button on the homepage.

Rules:
- Every MCQ and quick-recall item needs a unique `"id"` (e.g. `ULW2-LMCQ-01`). Progress and images depend on it.
- MCQ options must start with a letter: `"A. ..."`. `correct_answer` must start with the same letter.
- Do not put two files with the same `region` and `week`.
- If a file is invalid, it is skipped and listed under "Content files that were skipped" on the module page.

## Add images
1. Upload the image into `assets/Week2/` (PNG, JPG, JPEG or WEBP).
2. In that week's JSON, add an `"images"` list (add it right after the `"version"` line, and keep the comma):

```json
"images": [
  {
    "file": "Week2/painful_arc.png",
    "caption": "Painful arc",
    "description": "Pain between 60 and 120 degrees of abduction.",
    "source_file": "Applied Anatomy – Shoulder Joint",
    "source_page": 44,
    "related_type": "case",
    "related_id": "Mazin",
    "order": 1
  }
]
```

`related_type` and `related_id` decide where the image appears:

| related_type | related_id | Appears in |
|---|---|---|
| case | the case name, e.g. `Mazin` | that case |
| topic | the exact topic text of a case (`most_relevant_topic` or an anatomy link topic) | cases using that topic |
| question | a question `id`, e.g. `ULW1-LMCQ-04` | that MCQ or quick-recall question |
| section | `cases`, `mcqs` or `recall` | top of that tab |

`order` sorts images when several share the same place (smaller first).
A missing or wrong image path shows a small warning instead of crashing the app.
Keep images small (under about 500 KB) so they open fast on phones.

## Change the theme
- Colors and font: edit `.streamlit/config.toml`.
- Spacing and button size: edit `styles.css`.
- After editing: commit and push. On Streamlit Cloud, if the change does not appear, use the app menu to Reboot the app.
- Locally (Codespaces): stop with Ctrl+C and run `streamlit run app.py` again.