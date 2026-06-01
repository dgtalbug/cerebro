export async function exportPanelPdf(elementRef: React.RefObject<HTMLElement>, filename: string): Promise<void> {
  const { default: jsPDF } = await import("jspdf");
  const { default: html2canvas } = await import("html2canvas");

  const el = elementRef.current;
  if (!el) throw new Error("Element not found");

  const canvas = await html2canvas(el, { scale: 2, useCORS: true, backgroundColor: "#0a0d14" });
  const imgData = canvas.toDataURL("image/png");
  const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: [canvas.width / 2, canvas.height / 2] });
  pdf.addImage(imgData, "PNG", 0, 0, canvas.width / 2, canvas.height / 2);
  pdf.save(filename.endsWith(".pdf") ? filename : `${filename}.pdf`);
}

import type React from "react";
