# Report sources

Everything needed to regenerate the project report (.docx) lives in this
folder. The final documents are already built and included:

- `OKE_OVIGUERONYE_2026_PROJECT_REPORT.docx` — full project report
- `Chapter3_Chapter4_Report.docx` / `.pdf` — Chapters 3–4 only
- `Chapter5_Report.docx` — Chapter 5 only

## Rebuilding

Requires Node.js. From this folder:

```bash
npm install            # installs the "docx" package (first time only)
node build_report.js   # rebuilds Chapter3_Chapter4_Report.docx
node build_chapter5.js # rebuilds Chapter5_Report.docx
```

The diagrams and charts embedded in the report are in `report_assets/`;
`report_assets/make_diagrams.py` regenerates the charts from the trained
models' `metrics.json` files (needs the Python dependencies from the main
`requirements.txt`).
