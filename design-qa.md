# Interface verification

final result: passed

## Evidence and state

- Source visual truth: `/tmp/ev-campus-design/selected-design.png` (selected blue-and-white design).
- Desktop implementation: `/tmp/ev-campus-design/final-overview-zh.png`.
- Combined comparison: `/tmp/ev-campus-design/design-comparison.png`.
- Source and desktop implementation: 1374 × 1145 pixels; CSS viewport 1374 × 1145, density 1:1; no density resampling.
- Comparison state: overview, Chinese, all 1,200 records. English remains the default for a new session.
- Focused chart evidence: `/tmp/ev-campus-design/local-charts-zh.png`; prediction evidence: `/tmp/ev-campus-design/local-prediction.png`.
- Small-screen evidence: `/tmp/ev-campus-design/mobile-overview-fixed.png`, CSS viewport 390 × 844.
- Evidence files are local review captures, separate from runtime assets.

## Findings and fixes

1. [P2, resolved] Native radio circles weakened the top navigation. Styled the actual selected-tab element and retained keyboard-accessible native controls. The combined comparison shows the corrected underlined tabs.
2. [P2, resolved] Right-column chart labels were too small. Matplotlib figure widths now follow the column widths. Focused chart evidence shows readable legends and values.
3. [P2, resolved] Wide virtual-table content expanded the small-screen page. Clipped overflow at the records card; the main viewport and scroll width both measure 390 pixels after the fix. Table scrolling remains inside the table.

No actionable P0/P1/P2 findings remain in the checked states.

## Fidelity surfaces

- Typography: native sans-serif interface, clear title/KPI hierarchy, installed Chinese chart fallback; translated labels and legends render without clipping on desktop.
- Layout: white cards on pale blue, top navigation, four KPIs, horizontal desktop filters and two-column charts. Prediction inputs and results share the main page. Controls stack on small screens.
- Colours: blue interaction states, green/blue AC/DC marks, and green/amber/red observed and predicted status colours.
- Images: supplied original logo and official campus building/lake photograph; bundled files, correct subjects, sharp desktop banner crop.
- Copy: Chinese donut uses “条记录”; the hourly chart includes the 12:00–17:00 peak legend and shading. Units and estimate explanations are visible.

## Intentional changes from the reference

The requested 150-pixel photo, native Streamlit widgets, optional settings, real records table and working download replace the reference's static controls. Charts use actual filtered data. The table extends the page below the initial viewport. English is the initial language; Chinese was selected for the like-for-like visual comparison. Native fonts and component spacing are retained rather than reproducing every pixel of the static concept.

## Functional verification

- Default English, Chinese switch, stable translated choice values, no sidebar widgets.
- All-record KPIs checked against 1,200 rows; linked AC/peak filter gives 341 rows in charts and table.
- Four overview and six detailed charts, including battery temperature; empty filters show an empty table and explanation.
- Prediction form, saved model, three possible classes, calculated power/peak flag, and configurable high-temperature overstay warning.
- Download callback and original CSV column names; actual browser download is checked separately during cloud verification.
- Original dataset, saved model and evaluation outputs match their previous Git versions byte for byte.
- Browser console errors: none in the local checked session. Terminal checks passed; no persistent test script added.

## Implementation checklist

- [x] Bundle logo/photo and use project-relative paths.
- [x] Replace sidebar with horizontal navigation and main-page forms.
- [x] Link actual filters, charts, records and CSV download.
- [x] Compare desktop and focused states; fix small-screen overflow.
- [x] Preserve data, training outputs and calculation logic.

Cloud verification is performed after this version is pushed to the deployment branch. The local evidence above does not claim cloud execution.
