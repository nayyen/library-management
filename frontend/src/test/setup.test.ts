import { describe, expect, it } from "vitest";

/**
 * Sanity test confirming the vitest + jsdom + jest-dom harness loads —
 * gives `npx vitest run` something to collect/run in Wave 0 before any
 * real component tests exist (01-VALIDATION.md Wave 0 Requirements).
 */
describe("test harness setup", () => {
  it("loads jest-dom matchers and runs in a jsdom environment", () => {
    const el = document.createElement("div");
    el.textContent = "harness ok";
    document.body.appendChild(el);

    expect(el).toBeInTheDocument();
    expect(true).toBe(true);
  });
});
