import { describe, expect, it } from "vitest";

import { formatCount, formatPercent } from "./format";

describe("formatCount", () => {
  it("adds thousands separators", () => {
    expect(formatCount(1234)).toBe("1,234");
  });

  it("leaves small numbers unchanged", () => {
    expect(formatCount(187)).toBe("187");
  });
});

describe("formatPercent", () => {
  it("formats a fraction to one decimal by default", () => {
    expect(formatPercent(0.1234)).toBe("12.3%");
  });

  it("respects the digits argument", () => {
    expect(formatPercent(0.5, 0)).toBe("50%");
  });
});
