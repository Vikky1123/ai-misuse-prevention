/* Build Chapter 5 (Summary, Conclusion & Recommendations) .docx */
const fs = require("fs");
const path = require("path");
const H = require("./build_report_helpers.js");
const {
  Document, Packer, Paragraph, TextRun,
  AlignmentType, LevelFormat, HeadingLevel, PageBreak,
  ROOT,
  P, H1, H2, BULLET, NUM,
} = H;

const OUT5 = path.join(ROOT, "Chapter5_Report.docx");

// ===================================================================
// CHAPTER FIVE
// ===================================================================
const ch5 = [
  H1("CHAPTER FIVE: SUMMARY, CONCLUSION AND RECOMMENDATIONS"),

  H2("5.1 Summary"),
  P("This project set out to address a specific and growing gap in the moderation of generative artificial intelligence: existing defences are reactive, hash-based, and applied after harmful content has already been published, which makes them structurally unfit for diffusion models that synthesise a unique image on every generation. In response, the project designed, implemented, and evaluated an integrated three-layer framework for AI information misuse prevention that intervenes before generation, after generation, and at decision time."),
  P("Layer 1, a semantic prompt filter, fuses a learned TF-IDF and Logistic Regression classifier with a transparent, de-obfuscating regex signal layer to block harmful prompts before any image is produced, while correctly allowing benign prompts that reuse harmful vocabulary. Layer 2, a lightweight convolutional neural network trained on the CIFAKE dataset, detects the statistical artefacts of synthetic media rather than relying on known hashes, and falls back to a frequency-domain heuristic when the trained model is unavailable. Layer 3, a governance and logging package built on SQLite, converts numeric risk into operational severity, escalates the most serious harms for human review, and preserves a structured, machine-readable evidentiary record of every decision. A single Flask application orchestrates the three layers and exposes a pipeline page, an analyst dashboard, a per-case review page, and a model-performance page."),
  P("The system was evaluated end-to-end and per layer. Layer 1 achieved a 98.51% hold-out accuracy, a 98.70% (±0.68%) five-fold cross-validation accuracy on the cleaned and balanced 1,001-prompt dataset, and a perfect score on an independent 38-prompt challenge set. Layer 2 achieved a 95.39% test accuracy and a 0.9902 ROC-AUC on 10,000 held-out CIFAKE images, with balanced precision and recall across both classes. The full pipeline returned decisions in well under a second on commodity CPU hardware and logged every decision correctly for audit."),

  H2("5.2 Conclusion"),
  P("The project successfully demonstrates that AI misuse defence can be shifted from reactive, post-publication moderation to proactive, layered, and accountable prevention, and that this can be achieved on ordinary hardware without a GPU. Each layer addresses a failure mode the others cannot: Layer 1 prevents harmful prompts that Layer 2 would never see, Layer 2 catches synthetic images that arrive from outside the pipeline, and Layer 3 makes both decisions persistent, reviewable, and lawful."),
  P("Two findings stand out beyond the headline accuracy figures. First, data quality and quantity dominated the architecture lever: both learned layers improved most dramatically when their training data was cleaned and expanded rather than when their models were made more complex, with Layer 1's cross-validation spread falling from ±11.9% to ±0.68% after the prompt set was corrected and grown from 175 to 1,001 examples. Second, augmentation choices matter at the model-task boundary, since standard geometric augmentations smeared away the very high-frequency spectral fingerprints that Layer 2 depends on and had to be disabled. Taken together, the results validate the central thesis of the project: a layered, learned, and auditable system can deliver proactive prevention while producing the evidentiary record that regulators under the Nigeria Data Protection Act (2023) and the Cybercrimes (Amendment) Act (2024) require."),

  H2("5.3 Recommendations"),
  P("On the basis of the design experience and the evaluation results, the following recommendations are made for future work and deployment:"),
  NUM("Broaden the training distributions. Layer 1 should be extended with multilingual and code-switched prompts, and Layer 2 should be retrained on images from a wider range of generative models beyond Stable Diffusion so that detection generalises to newer diffusion and transformer-based generators."),
  NUM("Integrate a live image generator. The current system simulates generation as prevented when a prompt is blocked; a production deployment should wire Layer 1 directly in front of a real generation backend to demonstrate prevention on the live path."),
  NUM("Strengthen the governance layer. The SQLite store is well suited to a single-node prototype, but a multi-user deployment would benefit from a client-server database, authenticated analyst accounts, role-based access control, and tamper-evident logging for the evidentiary record."),
  NUM("Add continuous monitoring and retraining. Model performance should be tracked against live traffic, with periodic retraining triggered as new harmful phrasings and generation techniques emerge, so that the filters do not decay against an adversarial and evolving threat landscape."),
  NUM("Conduct adversarial red-teaming. A structured programme of adversarial testing, covering novel jailbreak phrasings and image-level evasion, should be undertaken to quantify robustness beyond the held-out and challenge sets used in this project."),
  NUM("Pursue independent security and legal review. Before any real-world use, the framework should undergo an external security audit and a review against the relevant data-protection and cybercrime statutes to confirm that the evidentiary record meets enforcement requirements in practice."),
];

// ===================================================================
// BUILD DOCUMENT
// ===================================================================
const doc = new Document({
  creator: "Oke Ovigueronye",
  title: "Chapter 5 — AI Misuse Prevention",
  description: "Summary, Conclusion and Recommendations",
  styles: {
    default: {
      document: { run: { font: "Times New Roman", size: 24 },
                  paragraph: { spacing: { line: 480 } } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Times New Roman", color: "000000" },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 360, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Times New Roman", color: "000000" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 2160 },
      },
    },
    children: [
      ...ch5,
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT5, buf);
  console.log("wrote", OUT5, "(" + buf.length + " bytes)");
});
